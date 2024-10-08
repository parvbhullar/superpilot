import concurrent.futures
import io
import json
import os
import string
import time
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timezone
from typing import Any
from typing import BinaryIO
from typing import cast
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import httpx
import requests
from retry import retry

from super_store.configs.app_configs import LOG_VESPA_TIMING_INFORMATION
from super_store.configs.app_configs import CLICKHOUSE_CONFIG_SERVER_HOST
from super_store.configs.app_configs import CLICKHOUSE_HOST
from super_store.configs.app_configs import CLICKHOUSE_PORT
from super_store.configs.app_configs import CLICKHOUSE_SCHEMA_PATH
from super_store.configs.chat_configs import DOC_TIME_DECAY
from super_store.configs.chat_configs import EDIT_KEYWORD_QUERY
from super_store.configs.chat_configs import HYBRID_ALPHA
from super_store.configs.chat_configs import NUM_RETURNED_HITS
from super_store.configs.chat_configs import TITLE_CONTENT_RATIO
from super_store.configs.constants import ACCESS_CONTROL_LIST
from super_store.configs.constants import UNPOD_HUB_ID
from super_store.configs.constants import UNPOD_KN_TOKEN
from super_store.configs.constants import BLURB
from super_store.configs.constants import BOOST
from super_store.configs.constants import CHUNK_ID
from super_store.configs.constants import CONTENT
from super_store.configs.constants import DOC_UPDATED_AT
from super_store.configs.constants import DOCUMENT_ID
from super_store.configs.constants import DOCUMENT_SETS
from super_store.configs.constants import EMBEDDINGS
from super_store.configs.constants import HIDDEN
from super_store.configs.constants import INDEX_SEPARATOR
from super_store.configs.constants import METADATA
from super_store.configs.constants import METADATA_LIST
from super_store.configs.constants import PRIMARY_OWNERS
from super_store.configs.constants import RECENCY_BIAS
from super_store.configs.constants import SECONDARY_OWNERS
from super_store.configs.constants import SECTION_CONTINUATION
from super_store.configs.constants import SEMANTIC_IDENTIFIER
from super_store.configs.constants import SKIP_TITLE_EMBEDDING
from super_store.configs.constants import SOURCE_LINKS
from super_store.configs.constants import SOURCE_TYPE
from super_store.configs.constants import TITLE
from super_store.configs.constants import TITLE_EMBEDDING
from super_store.configs.constants import TITLE_SEPARATOR
from super_store.configs.model_configs import SEARCH_DISTANCE_CUTOFF
from super_store.connectors.cross_connector_utils.miscellaneous_utils import (
    get_experts_stores_representations,
)
from super_store.document_index.document_index_utils import get_uuid_from_chunk
from super_store.document_index.interfaces import DocumentIndex
from super_store.document_index.interfaces import DocumentInsertionRecord
from super_store.document_index.interfaces import UpdateRequest
from super_store.document_index.vespa.utils import remove_invalid_unicode_chars
from super_store.document_index.vespa.utils import replace_invalid_doc_id_characters
from super_store.indexing.models import DocMetadataAwareIndexChunk
from super_store.search.models import IndexFilters
from super_store.search.models import InferenceChunk
from super_store.search.retrieval.search_runner import query_processing
from super_store.search.retrieval.search_runner import remove_stop_words_and_punctuation
from super_store.utils.batching import batch_generator
from super_store.utils.logger import setup_logger

logger = setup_logger()

CLICKHOUSE_DIM_REPLACEMENT_PAT = "VARIABLE_DIM"
UNPOD_CHUNK_REPLACEMENT_PAT = "UNPOD_CHUNK_NAME"
DOCUMENT_REPLACEMENT_PAT = "DOCUMENT_REPLACEMENT"
DATE_REPLACEMENT = "DATE_REPLACEMENT"
DOC_CLICKHOUSE_PORT = "DOC_CLICKHOUSE_PORT"

# config server
CLICKHOUSE_CONFIG_SERVER_URL = f"http://{CLICKHOUSE_CONFIG_SERVER_HOST}:{CLICKHOUSE_TENANT_PORT}"
CLICKHOUSE_APPLICATION_ENDPOINT = f"{CLICKHOUSE_CONFIG_SERVER_URL}/application/v2"

# main search application
CLICKHOUSE_APP_CONTAINER_URL = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}"
# unpod_chunk below is defined in clickhouse/app_configs/schemas/unpod_chunk.sd
DOCUMENT_ID_ENDPOINT = (
    f"{CLICKHOUSE_APP_CONTAINER_URL}/document/v1/default/{{index_name}}/docid"
)
SEARCH_ENDPOINT = f"{CLICKHOUSE_APP_CONTAINER_URL}/search/"

_BATCH_SIZE = 128  # Specific to ClickHouse
_NUM_THREADS = (
    32  # since ClickHouse doesn't allow batching of inserts / updates, we use threads
)
# up from 500ms for now, since we've seen quite a few timeouts
# in the long term, we are looking to improve the performance of ClickHouse
# so that we can bring this back to default
_CLICKHOUSE_TIMEOUT = "3s"
# Specific to ClickHouse, needed for highlighting matching keywords / section
CONTENT_SUMMARY = "content_summary"


@dataclass
class _ClickHouseUpdateRequest:
    document_id: str
    url: str
    update_request: dict[str, dict]


@retry(tries=3, delay=1, backoff=2)
def _does_document_exist(
    doc_chunk_id: str,
    index_name: str,
    http_client: httpx.Client,
) -> bool:
    """Returns whether the document already exists and the users/group whitelists
    Specifically in this case, document refers to a clickhouse document which is equivalent to a Unpod
    chunk. This checks for whether the chunk exists already in the index"""
    doc_url = f"{DOCUMENT_ID_ENDPOINT.format(index_name=index_name)}/{doc_chunk_id}"
    print("ClickHouse UR:", doc_url)
    doc_fetch_response = http_client.get(doc_url)
    if doc_fetch_response.status_code == 404:
        return False

    if doc_fetch_response.status_code != 200:
        logger.debug(f"Failed to check for document with URL {doc_url}")
        raise RuntimeError(
            f"Unexpected fetch document by ID value from ClickHouse "
            f"with error {doc_fetch_response.status_code}"
        )
    return True


def _clickhouse_get_updated_at_attribute(t: datetime | None) -> int | None:
    if not t:
        return None

    if t.tzinfo != timezone.utc:
        raise ValueError("Connectors must provide document update time in UTC")

    return int(t.timestamp())


def _get_clickhouse_chunks_by_document_id(
    document_id: str,
    index_name: str,
    user_access_control_list: list[str] | None = None,
    min_chunk_ind: int | None = None,
    max_chunk_ind: int | None = None,
    field_names: list[str] | None = None,
) -> list[dict]:
    # Constructing the URL for the Visit API
    # NOTE: visit API uses the same URL as the document API, but with different params
    url = DOCUMENT_ID_ENDPOINT.format(index_name=index_name)

    # build the list of fields to retrieve
    field_set_list = (
        None
        if not field_names
        else [f"{index_name}:{field_name}" for field_name in field_names]
    )
    acl_fieldset_entry = f"{index_name}:{ACCESS_CONTROL_LIST}"
    if (
        field_set_list
        and user_access_control_list
        and acl_fieldset_entry not in field_set_list
    ):
        field_set_list.append(acl_fieldset_entry)
    field_set = ",".join(field_set_list) if field_set_list else None

    # build filters
    selection = f"{index_name}.document_id=='{document_id}'"
    if min_chunk_ind is not None:
        selection += f" and {index_name}.chunk_id>={min_chunk_ind}"
    if max_chunk_ind is not None:
        selection += f" and {index_name}.chunk_id<={max_chunk_ind}"

    # Setting up the selection criteria in the query parameters
    params = {
        # NOTE: Document Selector Language doesn't allow `contains`, so we can't check
        # for the ACL in the selection. Instead, we have to check as a postfilter
        "selection": selection,
        "continuation": None,
        "wantedDocumentCount": 1_000,
        "fieldSet": field_set,
    }

    document_chunks: list[dict] = []
    while True:
        response = requests.get(url, params=params)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            request_info = f"Headers: {response.request.headers}\nPayload: {params}"
            response_info = f"Status Code: {response.status_code}\nResponse Content: {response.text}"
            error_base = f"Error occurred getting chunk by Document ID {document_id}"
            logger.error(
                f"{error_base}:\n"
                f"{request_info}\n"
                f"{response_info}\n"
                f"Exception: {e}"
            )
            raise requests.HTTPError(error_base) from e

        # Check if the response contains any documents
        response_data = response.json()
        if "documents" in response_data:
            for document in response_data["documents"]:
                if user_access_control_list:
                    document_acl = document["fields"].get(ACCESS_CONTROL_LIST)
                    if not document_acl or not any(
                        user_acl_entry in document_acl
                        for user_acl_entry in user_access_control_list
                    ):
                        continue
                document_chunks.append(document)
            document_chunks.extend(response_data["documents"])

        # Check for continuation token to handle pagination
        if "continuation" in response_data and response_data["continuation"]:
            params["continuation"] = response_data["continuation"]
        else:
            break  # Exit loop if no continuation token

    return document_chunks


def _get_clickhouse_chunk_ids_by_document_id(
    document_id: str, index_name: str, user_access_control_list: list[str] | None = None
) -> list[str]:
    document_chunks = _get_clickhouse_chunks_by_document_id(
        document_id=document_id,
        index_name=index_name,
        user_access_control_list=user_access_control_list,
        field_names=[DOCUMENT_ID],
    )
    return [chunk["id"].split("::", 1)[-1] for chunk in document_chunks]


@retry(tries=3, delay=1, backoff=2)
def _delete_clickhouse_doc_chunks(
    document_id: str, index_name: str, http_client: httpx.Client
) -> None:
    doc_chunk_ids = _get_clickhouse_chunk_ids_by_document_id(
        document_id=document_id, index_name=index_name
    )

    for chunk_id in doc_chunk_ids:
        try:
            res = http_client.delete(
                f"{DOCUMENT_ID_ENDPOINT.format(index_name=index_name)}/{chunk_id}"
            )
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to delete chunk, details: {e.response.text}")
            raise


def _delete_clickhouse_docs(
    document_ids: list[str],
    index_name: str,
    http_client: httpx.Client,
    executor: concurrent.futures.ThreadPoolExecutor | None = None,
) -> None:
    external_executor = True

    if not executor:
        external_executor = False
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=_NUM_THREADS)

    try:
        doc_deletion_future = {
            executor.submit(
                _delete_clickhouse_doc_chunks, doc_id, index_name, http_client
            ): doc_id
            for doc_id in document_ids
        }
        for future in concurrent.futures.as_completed(doc_deletion_future):
            # Will raise exception if the deletion raised an exception
            future.result()

    finally:
        if not external_executor:
            executor.shutdown(wait=True)


def _get_existing_documents_from_chunks(
    chunks: list[DocMetadataAwareIndexChunk],
    index_name: str,
    http_client: httpx.Client,
    executor: concurrent.futures.ThreadPoolExecutor | None = None,
) -> set[str]:
    external_executor = True

    if not executor:
        external_executor = False
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=_NUM_THREADS)

    document_ids: set[str] = set()
    try:
        chunk_existence_future = {
            executor.submit(
                _does_document_exist,
                str(get_uuid_from_chunk(chunk)),
                index_name,
                http_client,
            ): chunk
            for chunk in chunks
        }
        for future in concurrent.futures.as_completed(chunk_existence_future):
            chunk = chunk_existence_future[future]
            chunk_already_existed = future.result()
            if chunk_already_existed:
                document_ids.add(chunk.source_document.id)

    finally:
        if not external_executor:
            executor.shutdown(wait=True)

    return document_ids


@retry(tries=3, delay=1, backoff=2)
def _index_clickhouse_chunk(
    chunk: DocMetadataAwareIndexChunk, index_name: str, http_client: httpx.Client
) -> None:
    json_header = {
        "Content-Type": "application/json",
    }
    document = chunk.source_document
    # No minichunk documents in clickhouse, minichunk vectors are stored in the chunk itself
    clickhouse_chunk_id = str(get_uuid_from_chunk(chunk))

    embeddings = chunk.embeddings
    embeddings_name_vector_map = {"full_chunk": embeddings.full_embedding}
    if embeddings.mini_chunk_embeddings:
        for ind, m_c_embed in enumerate(embeddings.mini_chunk_embeddings):
            embeddings_name_vector_map[f"mini_chunk_{ind}"] = m_c_embed

    title = document.get_title_for_document_index()

    clickhouse_document_fields = {
        DOCUMENT_ID: document.id,
        CHUNK_ID: chunk.chunk_id,
        BLURB: remove_invalid_unicode_chars(chunk.blurb),
        TITLE: remove_invalid_unicode_chars(title) if title else None,
        SKIP_TITLE_EMBEDDING: not title,
        CONTENT: remove_invalid_unicode_chars(chunk.content),
        # This duplication of `content` is needed for keyword highlighting :(
        CONTENT_SUMMARY: remove_invalid_unicode_chars(chunk.content),
        SOURCE_TYPE: str(document.source.value),
        SOURCE_LINKS: json.dumps(chunk.source_links),
        SEMANTIC_IDENTIFIER: remove_invalid_unicode_chars(document.semantic_identifier),
        SECTION_CONTINUATION: chunk.section_continuation,
        METADATA: json.dumps(document.metadata),
        # Save as a list for efficient extraction as an Attribute
        METADATA_LIST: chunk.source_document.get_metadata_str_attributes(),
        EMBEDDINGS: embeddings_name_vector_map,
        TITLE_EMBEDDING: chunk.title_embedding,
        BOOST: chunk.boost,
        DOC_UPDATED_AT: _clickhouse_get_updated_at_attribute(document.doc_updated_at),
        PRIMARY_OWNERS: get_experts_stores_representations(document.primary_owners),
        SECONDARY_OWNERS: get_experts_stores_representations(document.secondary_owners),
        # the only `set` clickhouse has is `weightedset`, so we have to give each
        # element an arbitrary weight
        ACCESS_CONTROL_LIST: {acl_entry: 1 for acl_entry in chunk.access.to_acl()},
        DOCUMENT_SETS: {document_set: 1 for document_set in chunk.document_sets},
        UNPOD_HUB_ID: chunk.source_document.hub_id,
        UNPOD_KN_TOKEN: chunk.source_document.kn_token
    }

    clickhouse_url = f"{DOCUMENT_ID_ENDPOINT.format(index_name=index_name)}/{clickhouse_chunk_id}"
    logger.debug(f'Indexing to URL "{clickhouse_url}"')
    res = http_client.post(
        clickhouse_url, headers=json_header, json={"fields": clickhouse_document_fields}
    )
    try:
        res.raise_for_status()
    except Exception as e:
        logger.exception(
            f"Failed to index document: '{document.id}'. Got response: '{res.text}'"
        )
        raise e


def _batch_index_clickhouse_chunks(
    chunks: list[DocMetadataAwareIndexChunk],
    index_name: str,
    http_client: httpx.Client,
    executor: concurrent.futures.ThreadPoolExecutor | None = None,
) -> None:
    external_executor = True

    if not executor:
        external_executor = False
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=_NUM_THREADS)

    try:
        chunk_index_future = {
            executor.submit(_index_clickhouse_chunk, chunk, index_name, http_client): chunk
            for chunk in chunks
        }
        for future in concurrent.futures.as_completed(chunk_index_future):
            # Will raise exception if any indexing raised an exception
            future.result()

    finally:
        if not external_executor:
            executor.shutdown(wait=True)


def _clear_and_index_clickhouse_chunks(
    chunks: list[DocMetadataAwareIndexChunk],
    index_name: str,
) -> set[DocumentInsertionRecord]:
    """Receive a list of chunks from a batch of documents and index the chunks into ClickHouse along
    with updating the associated permissions. Assumes that a document will not be split into
    multiple chunk batches calling this function multiple times, otherwise only the last set of
    chunks will be kept"""
    existing_docs: set[str] = set()

    # NOTE: using `httpx` here since `requests` doesn't support HTTP2. This is beneficial for
    # indexing / updates / deletes since we have to make a large volume of requests.
    with (
        concurrent.futures.ThreadPoolExecutor(max_workers=_NUM_THREADS) as executor,
        httpx.Client(http2=True) as http_client,
    ):
        # Check for existing documents, existing documents need to have all of their chunks deleted
        # prior to indexing as the document size (num chunks) may have shrunk
        first_chunks = [chunk for chunk in chunks if chunk.chunk_id == 0]
        for chunk_batch in batch_generator(first_chunks, _BATCH_SIZE):
            existing_docs.update(
                _get_existing_documents_from_chunks(
                    chunks=chunk_batch,
                    index_name=index_name,
                    http_client=http_client,
                    executor=executor,
                )
            )

        for doc_id_batch in batch_generator(existing_docs, _BATCH_SIZE):
            _delete_clickhouse_docs(
                document_ids=doc_id_batch,
                index_name=index_name,
                http_client=http_client,
                executor=executor,
            )

        for chunk_batch in batch_generator(chunks, _BATCH_SIZE):
            _batch_index_clickhouse_chunks(
                chunks=chunk_batch,
                index_name=index_name,
                http_client=http_client,
                executor=executor,
            )

    all_doc_ids = {chunk.source_document.id for chunk in chunks}

    return {
        DocumentInsertionRecord(
            document_id=doc_id,
            already_existed=doc_id in existing_docs,
        )
        for doc_id in all_doc_ids
    }


def _build_clickhouse_filters(filters: IndexFilters, include_hidden: bool = False) -> str:
    def _build_or_filters(key: str, vals: list[str] | None) -> str:
        if vals is None:
            return ""

        valid_vals = [val for val in vals if val]
        if not key or not valid_vals:
            return ""

        eq_elems = [f'{key} contains "{elem}"' for elem in valid_vals]
        or_clause = " or ".join(eq_elems)
        return f"({or_clause}) and "

    def _build_time_filter(
        cutoff: datetime | None,
        # Slightly over 3 Months, approximately 1 fiscal quarter
        untimed_doc_cutoff: timedelta = timedelta(days=92),
    ) -> str:
        if not cutoff:
            return ""

        # For Documents that don't have an updated at, filter them out for queries asking for
        # very recent documents (3 months) default. Documents that don't have an updated at
        # time are assigned 3 months for time decay value
        include_untimed = datetime.now(timezone.utc) - untimed_doc_cutoff > cutoff
        cutoff_secs = int(cutoff.timestamp())

        if include_untimed:
            # Documents without updated_at are assigned -1 as their date
            return f"!({DOC_UPDATED_AT} < {cutoff_secs}) and "

        return f"({DOC_UPDATED_AT} >= {cutoff_secs}) and "

    filter_str = f"!({HIDDEN}=true) and " if not include_hidden else ""

    # CAREFUL touching this one, currently there is no second ACL double-check post retrieval
    if filters.access_control_list is not None:
        filter_str += _build_or_filters(
            ACCESS_CONTROL_LIST, filters.access_control_list
        )

    source_strs = (
        [s.value for s in filters.source_type] if filters.source_type else None
    )
    filter_str += _build_or_filters(SOURCE_TYPE, source_strs)

    tag_attributes = None
    tags = filters.tags
    if tags:
        tag_attributes = [tag.tag_key + INDEX_SEPARATOR + tag.tag_value for tag in tags]
    filter_str += _build_or_filters(METADATA_LIST, tag_attributes)

    filter_str += _build_or_filters(DOCUMENT_SETS, filters.document_set)

    filter_str += _build_time_filter(filters.time_cutoff)

    return filter_str


def _process_dynamic_summary(
    dynamic_summary: str, max_summary_length: int = 400
) -> list[str]:
    if not dynamic_summary:
        return []

    current_length = 0
    processed_summary: list[str] = []
    for summary_section in dynamic_summary.split("<sep />"):
        # if we're past the desired max length, break at the last word
        if current_length + len(summary_section) >= max_summary_length:
            summary_section = summary_section[: max_summary_length - current_length]
            summary_section = summary_section.lstrip()  # remove any leading whitespace

            # handle the case where the truncated section is either just a
            # single (partial) word or if it's empty
            first_space = summary_section.find(" ")
            if first_space == -1:
                # add ``...`` to previous section
                if processed_summary:
                    processed_summary[-1] += "..."
                break

            # handle the valid truncated section case
            summary_section = summary_section.rsplit(" ", 1)[0]
            if summary_section[-1] in string.punctuation:
                summary_section = summary_section[:-1]
            summary_section += "..."
            processed_summary.append(summary_section)
            break

        processed_summary.append(summary_section)
        current_length += len(summary_section)

    return processed_summary


def _clickhouse_hit_to_inference_chunk(hit: dict[str, Any]) -> InferenceChunk:
    fields = cast(dict[str, Any], hit["fields"])

    # parse fields that are stored as strings, but are really json / datetime
    metadata = json.loads(fields[METADATA]) if METADATA in fields else {}
    updated_at = (
        datetime.fromtimestamp(fields[DOC_UPDATED_AT], tz=timezone.utc)
        if DOC_UPDATED_AT in fields
        else None
    )

    # The highlights might include the title but this is the best way we have so far to show the highlighting
    match_highlights = _process_dynamic_summary(
        # fallback to regular `content` if the `content_summary` field
        # isn't present
        dynamic_summary=hit["fields"].get(CONTENT_SUMMARY, hit["fields"][CONTENT]),
    )
    semantic_identifier = fields.get(SEMANTIC_IDENTIFIER, "")
    if not semantic_identifier:
        logger.error(
            f"Chunk with blurb: {fields.get(BLURB, 'Unknown')[:50]}... has no Semantic Identifier"
        )

    # Remove the title from the first chunk as every chunk already included
    # its semantic identifier for LLM
    content = fields[CONTENT]
    if fields[CHUNK_ID] == 0:
        parts = content.split(TITLE_SEPARATOR, maxsplit=1)
        content = parts[1] if len(parts) > 1 and "\n" not in parts[0] else content

    # User ran into this, not sure why this could happen, error checking here
    blurb = fields.get(BLURB)
    if not blurb:
        logger.error(f"Chunk with id {fields.get(semantic_identifier)} ")
        blurb = ""

    source_links = fields.get(SOURCE_LINKS, {})
    source_links_dict_unprocessed = (
        json.loads(source_links) if isinstance(source_links, str) else source_links
    )
    source_links_dict = {
        int(k): v
        for k, v in cast(dict[str, str], source_links_dict_unprocessed).items()
    }

    return InferenceChunk(
        chunk_id=fields[CHUNK_ID],
        blurb=blurb,
        content=content,
        source_links=source_links_dict,
        section_continuation=fields[SECTION_CONTINUATION],
        document_id=fields[DOCUMENT_ID],
        source_type=fields[SOURCE_TYPE],
        semantic_identifier=fields[SEMANTIC_IDENTIFIER],
        boost=fields.get(BOOST, 1),
        recency_bias=fields.get("matchfeatures", {}).get(RECENCY_BIAS, 1.0),
        score=hit.get("relevance", 0),
        hidden=fields.get(HIDDEN, False),
        primary_owners=fields.get(PRIMARY_OWNERS),
        secondary_owners=fields.get(SECONDARY_OWNERS),
        metadata=metadata,
        match_highlights=match_highlights,
        updated_at=updated_at,
    )


@retry(tries=3, delay=1, backoff=2)
def _query_clickhouse(query_params: Mapping[str, str | int | float]) -> list[InferenceChunk]:
    if "query" in query_params and not cast(str, query_params["query"]).strip():
        raise ValueError("No/empty query received")

    params = dict(
        **query_params,
        **{
            "presentation.timing": True,
        }
        if LOG_VESPA_TIMING_INFORMATION
        else {},
    )

    response = requests.post(
        SEARCH_ENDPOINT,
        json=params,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        request_info = f"Headers: {response.request.headers}\nPayload: {params}"
        response_info = (
            f"Status Code: {response.status_code}\n"
            f"Response Content: {response.text}"
        )
        error_base = "Failed to query ClickHouse"
        logger.error(
            f"{error_base}:\n"
            f"{request_info}\n"
            f"{response_info}\n"
            f"Exception: {e}"
        )
        raise requests.HTTPError(error_base) from e

    response_json: dict[str, Any] = response.json()
    if LOG_VESPA_TIMING_INFORMATION:
        logger.info("ClickHouse timing info: %s", response_json.get("timing"))
    hits = response_json["root"].get("children", [])

    for hit in hits:
        if hit["fields"].get(CONTENT) is None:
            identifier = hit["fields"].get("documentid") or hit["id"]
            logger.error(
                f"ClickHouse Index with ClickHouse ID {identifier} has no contents. "
                f"This is invalid because the vector is not meaningful and keywordsearch cannot "
                f"fetch this document"
            )

    filtered_hits = [hit for hit in hits if hit["fields"].get(CONTENT) is not None]

    inference_chunks = [_clickhouse_hit_to_inference_chunk(hit) for hit in filtered_hits]
    # Good Debugging Spot
    return inference_chunks


@retry(tries=3, delay=1, backoff=2)
def _inference_chunk_by_clickhouse_id(clickhouse_id: str, index_name: str) -> InferenceChunk:
    res = requests.get(
        f"{DOCUMENT_ID_ENDPOINT.format(index_name=index_name)}/{clickhouse_id}"
    )
    res.raise_for_status()

    return _clickhouse_hit_to_inference_chunk(res.json())


def in_memory_zip_from_file_bytes(file_contents: dict[str, bytes]) -> BinaryIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in file_contents.items():
            zipf.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer


def _create_document_xml_lines(doc_names: list[str | None]) -> str:
    doc_lines = [
        f'<document type="{doc_name}" mode="index" />'
        for doc_name in doc_names
        if doc_name
    ]
    return "\n".join(doc_lines)


def _clean_chunk_id_copy(
    chunk: DocMetadataAwareIndexChunk,
) -> DocMetadataAwareIndexChunk:
    clean_chunk = chunk.copy(
        update={
            "source_document": chunk.source_document.copy(
                update={
                    "id": replace_invalid_doc_id_characters(chunk.source_document.id)
                }
            )
        }
    )
    return clean_chunk


class ClickHouseIndex(DocumentIndex):
    sql_base = (
        f"SELECT "
        f"documentid, "
        f"{DOCUMENT_ID}, "
        f"{CHUNK_ID}, "
        f"{BLURB}, "
        f"{CONTENT}, "
        f"{SOURCE_TYPE}, "
        f"{SOURCE_LINKS}, "
        f"{SEMANTIC_IDENTIFIER}, "
        f"{SECTION_CONTINUATION}, "
        f"{BOOST}, "
        f"{HIDDEN}, "
        f"{DOC_UPDATED_AT}, "
        f"{PRIMARY_OWNERS}, "
        f"{SECONDARY_OWNERS}, "
        f"{METADATA}, "
        f"{CONTENT_SUMMARY} "
        f"FROM {{index_name}} WHERE "
    )

    def __init__(self, index_name: str, secondary_index_name: Optional[str] = None) -> None:
        self.index_name = index_name
        self.secondary_index_name = secondary_index_name

    def ensure_indices_exist(
        self,
        index_embedding_dim: int,
        secondary_index_embedding_dim: Optional[int] = None,
    ) -> None:
        # In ClickHouse, you might create a table instead of preparing a schema for Vespa
        print(f"Ensuring ClickHouse index for {self.index_name} exists.")

        # vespa_schema_path = VESPA_SCHEMA_PATH
        # schema_file = os.path.join(vespa_schema_path, "schemas", "unpod_chunk.sd")
        schema = {}
        # Example: creating tables if they don't exist
        # For demonstration purposes, this assumes a function `create_clickhouse_table` exists
        create_clickhouse_table(self.index_name, index_embedding_dim, schema)

        # For clickhouse we don't need second table
        # if self.secondary_index_name and secondary_index_embedding_dim:
        #     create_clickhouse_table(self.secondary_index_name, secondary_index_embedding_dim, schema)

    def index(
        self,
        chunks: List[DocMetadataAwareIndexChunk],
    ) -> set:
        # Insert chunks into ClickHouse table
        cleaned_chunks = [_clean_chunk_id_copy(chunk) for chunk in chunks]
        return _clear_and_index_clickhouse_chunks(
            chunks=cleaned_chunks, index_name=self.index_name
        )

    @staticmethod
    def _apply_updates_batched(
        updates: List[_ClickHouseUpdateRequest],
        batch_size: int = _BATCH_SIZE,
    ) -> None:
        # # Update logic for ClickHouse
        # with concurrent.futures.ThreadPoolExecutor(max_workers=_NUM_THREADS) as executor:
        #     for update_batch in batch_generator(updates, batch_size):
        #         executor.map(_update_clickhouse_chunk, update_batch)

        def _update_chunk(
                update: _ClickHouseUpdateRequest, http_client: httpx.Client
        ) -> httpx.Response:
            logger.debug(
                f"Updating with request to {update.url} with body {update.update_request}"
            )
            return http_client.put(
                update.url,
                headers={"Content-Type": "application/json"},
                json=update.update_request,
            )

            # NOTE: using `httpx` here since `requests` doesn't support HTTP2. This is beneficient for
            # indexing / updates / deletes since we have to make a large volume of requests.

        with (
            concurrent.futures.ThreadPoolExecutor(max_workers=_NUM_THREADS) as executor,
            httpx.Client(http2=True) as http_client,
        ):
            for update_batch in batch_generator(updates, batch_size):
                future_to_document_id = {
                    executor.submit(
                        _update_chunk,
                        update,
                        http_client,
                    ): update.document_id
                    for update in update_batch
                }
                for future in concurrent.futures.as_completed(future_to_document_id):
                    res = future.result()
                    try:
                        res.raise_for_status()
                    except requests.HTTPError as e:
                        failure_msg = f"Failed to update document: {future_to_document_id[future]}"
                        raise requests.HTTPError(failure_msg) from e

    def update(self, update_requests: List[UpdateRequest]) -> None:
        logger.info(f"Updating {len(update_requests)} documents in ClickHouse")

        for update_request in update_requests:
            update_request.document_ids = [
                replace_invalid_doc_id_characters(doc_id)
                for doc_id in update_request.document_ids
            ]

        processed_updates_requests: List[_ClickHouseUpdateRequest] = []

        # Fetch all chunks for each document ahead of time
        index_names = [self.index_name]
        if self.secondary_index_name:
            index_names.append(self.secondary_index_name)

        with concurrent.futures.ThreadPoolExecutor(max_workers=_NUM_THREADS) as executor:
            for update_request in update_requests:
                for document_id in update_request.document_ids:
                    for index_name in index_names:
                        doc_chunk_ids = _get_clickhouse_chunk_ids_by_document_id(document_id, index_name)
                        for doc_chunk_id in doc_chunk_ids:
                            processed_updates_requests.append(
                                _ClickHouseUpdateRequest(
                                    document_id=document_id,
                                    url=f"{index_name}/{doc_chunk_id}",
                                    update_request=self._build_update_request(update_request),
                                )
                            )

        self._apply_updates_batched(processed_updates_requests)
        logger.info("Finished updating ClickHouse documents.")

    def _build_update_request(self, update_request: UpdateRequest) -> dict:
        update_dict: Dict[str, dict] = {"fields": {}}
        if update_request.boost is not None:
            update_dict["fields"][BOOST] = {"assign": update_request.boost}
        if update_request.document_sets is not None:
            update_dict["fields"][DOCUMENT_SETS] = {
                "assign": {document_set: 1 for document_set in update_request.document_sets}
            }
        if update_request.access is not None:
            update_dict["fields"][ACCESS_CONTROL_LIST] = {
                "assign": {acl_entry: 1 for acl_entry in update_request.access.to_acl()}
            }
        if update_request.hidden is not None:
            update_dict["fields"][HIDDEN] = {"assign": update_request.hidden}
        return update_dict

    def delete(self, doc_ids: List[str]) -> None:
        logger.info(f"Deleting {len(doc_ids)} documents from ClickHouse")
        doc_ids = [replace_invalid_doc_id_characters(doc_id) for doc_id in doc_ids]
        for index_name in [self.index_name, self.secondary_index_name]:
            if index_name:
                _delete_clickhouse_docs(document_ids=doc_ids, index_name=index_name)

    def id_based_retrieval(
        self,
        document_id: str,
        min_chunk_ind: Optional[int] = None,
        max_chunk_ind: Optional[int] = None,
        user_access_control_list: Optional[List[str]] = None,
    ) -> List[InferenceChunk]:
        document_id = replace_invalid_doc_id_characters(document_id)

        clickhouse_chunks = _get_clickhouse_chunks_by_document_id(
            document_id=document_id,
            index_name=self.index_name,
            user_access_control_list=user_access_control_list,
            min_chunk_ind=min_chunk_ind,
            max_chunk_ind=max_chunk_ind,
        )

        if not clickhouse_chunks:
            return []

        inference_chunks = [
            _clickhouse_hit_to_inference_chunk(chunk) for chunk in clickhouse_chunks
        ]
        inference_chunks.sort(key=lambda chunk: chunk.chunk_id)
        return inference_chunks

    def keyword_retrieval(
        self,
        query: str,
        filters: IndexFilters,
        time_decay_multiplier: float,
        num_to_retrieve: int = NUM_RETURNED_HITS,
        offset: int = 0,
        edit_keyword_query: bool = EDIT_KEYWORD_QUERY,
    ) -> List[InferenceChunk]:
        sql_where_clauses = _build_clickhouse_filters(filters)
        sql = (
            ClickhouseIndex.sql_base.format(index_name=self.index_name)
            + sql_where_clauses
            + f"AND match(content_summary, '{query}') "
        )

        final_query = query_processing(query) if edit_keyword_query else query

        params = {
            "sql": sql,
            "query": final_query,
            "hits": num_to_retrieve,
            "offset": offset,
        }

        return _query_clickhouse(params)

    def semantic_retrieval(
        self,
        query: str,
        query_embedding: List[float],
        filters: IndexFilters,
        time_decay_multiplier: float,
        num_to_retrieve: int = NUM_RETURNED_HITS,
        offset: int = 0,
        distance_cutoff: Optional[float] = SEARCH_DISTANCE_CUTOFF,
        edit_keyword_query: bool = EDIT_KEYWORD_QUERY,
    ) -> List[InferenceChunk]:
        sql_where_clauses = _build_clickhouse_filters(filters)
        sql = (
            ClickhouseIndex.sql_base.format(index_name=self.index_name)
            + sql_where_clauses
            + f"AND cosineDistance(embeddings, {query_embedding}) < {distance_cutoff} "
            + f"AND match(content_summary, '{query}') "
        )

        query_keywords = (
            " ".join(remove_stop_words_and_punctuation(query))
            if edit_keyword_query
            else query
        )

        params = {
            "sql": sql,
            "query": query_keywords,
            "hits": num_to_retrieve,
            "offset": offset,
        }

        return _query_clickhouse(params)

    def hybrid_retrieval(
        self,
        query: str,
        query_embedding: List[float],
        filters: IndexFilters,
        time_decay_multiplier: float,
        num_to_retrieve: int,
        offset: int = 0,
        hybrid_alpha: Optional[float] = HYBRID_ALPHA,
        title_content_ratio: Optional[float] = TITLE_CONTENT_RATIO,
        distance_cutoff: Optional[float] = SEARCH_DISTANCE_CUTOFF,
        edit_keyword_query: bool = EDIT_KEYWORD_QUERY,
    ) -> List[InferenceChunk]:
        sql_where_clauses = _build_clickhouse_filters(filters)
        sql = (
            ClickhouseIndex.sql_base.format(index_name=self.index_name)
            + sql_where_clauses
            + f"AND cosineDistance(embeddings, {query_embedding}) < {distance_cutoff} "
            + f"AND match(content_summary, '{query}') "
        )

        query_keywords = (
            " ".join(remove_stop_words_and_punctuation(query))
            if edit_keyword_query
            else query
        )

        params = {
            "sql": sql,
            "query": query_keywords,
            "hits": num_to_retrieve,
            "offset": offset,
            "hybrid_alpha": hybrid_alpha if hybrid_alpha is not None else HYBRID_ALPHA,
            "title_content_ratio": title_content_ratio
            if title_content_ratio is not None
            else TITLE_CONTENT_RATIO,
        }

        return _query_clickhouse(params)

    def admin_retrieval(
        self,
        query: str,
        filters: IndexFilters,
        num_to_retrieve: int = NUM_RETURNED_HITS,
        offset: int = 0,
    ) -> List[InferenceChunk]:
        sql_where_clauses = _build_clickhouse_filters(filters, include_hidden=True)
        sql = (
            ClickhouseIndex.sql_base.format(index_name=self.index_name)
            + sql_where_clauses
            + f"AND match(content_summary, '{query}') "
        )

        params = {
            "sql": sql,
            "query": query,
            "hits": num_to_retrieve,
            "offset": offset,
        }

        return _query_clickhouse(params)

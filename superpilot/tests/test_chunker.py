import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from super_store.indexing.indexing_pipeline import (
    build_indexing_pipeline,
)
from sqlalchemy.orm import Session

from super_store.document_index.factory import (
    get_default_document_index,
)
from super_store.db.embedding_model import (
    get_current_db_embedding_model,
    get_secondary_db_embedding_model,
)
from super_store.indexing.embedder import (
    DefaultIndexingEmbedder,
)

from itertools import chain
from super_store.connectors.file.connector import (
    LocalFileConnector,
)

import uuid
from super_store.schema import SchemaCreator
from super_store.connectors.models import (
    Document,
    Section,
    IndexAttemptMetadata,
)
from super_store.indexing.chunker import (
    DefaultChunker,
)
from super_store.indexing.models import DocAwareChunk
from super_store.parsers.utils.file import compute_sha1_from_content
from services.store_service.core.datetime import get_datetime_now
from super_store.parser import FileParser
from super_store.db.engine import get_postgres_session

from super_store.search.models import (
    IndexFilters,
    SearchDoc,
)
from super_store.search.utils import (
    chunks_or_sections_to_search_docs,
)
from super_store.server.query_and_chat.models import (
    AdminSearchRequest,
    AdminSearchResponse,
)


def toDocument(row, **metadata):
    sections = []
    content = ""
    for i, (k, v) in enumerate(row.items()):
        sections.append(Section(text=f"{k}:{v}", link=None))
        content += f"{k}:{v}\n"
    sha1 = compute_sha1_from_content(content.encode())
    doc = Document(
        id=uuid.uuid1().hex,
        source="file",
        from_ingestion_api=True,
        sections=sections,
        metadata={"source": "file", **metadata},
        semantic_identifier=sha1,
        doc_updated_at=get_datetime_now(),
    )
    print(doc.to_short_descriptor())
    return doc


async def main():
    file_name = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/store-service/ai-tutor_response_20240517-110617_Humanities.csv"
    parser = FileParser()
    schema_creator = SchemaCreator()
    processed_data = await parser.read_data_file(file_name, None, load_only=True)
    is_success = processed_data.get("success", False)
    if not is_success:
        return processed_data
    data = processed_data.get("data", {}).get("docs", [])
    schema = processed_data.get("data", {}).get("columns", {})
    json_schema = schema_creator.create_schema(schema)
    documents = []
    for row in data:
        document = toDocument(
            row, json_schema=str(json_schema), filename=os.path.basename(file_name)
        )
        documents.append(document)
    print(len(documents))
    chunker = DefaultChunker()
    t1 = time.time()
    chunks: list[DocAwareChunk] = list(
        chain(*[chunker.chunk(document=document) for document in documents[:10]])
    )
    print(f"Number of chunks: {len(chunks)}")
    for ch in chunks:
        print(str(ch) + "\n")
    t2 = time.time()
    print("Time Taken", round(t2 - t1))


def use_file_connector():
    file_name = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/store-service/test/data/ai-tutor_response_20240517-110617_Humanities.csv"
    file_name = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/store-service/test/data/Amazon EC2 Instance Comparison.csv"
    # file_name = "/home/mastersindia/Documents/Personal/Knowledge/store-service/ai-tutor_response_20240517-110617_Humanities.csv"
    file_name = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/store-service/test/data/Copy of AI Answer 5M Scraping - Master - AI-Tutor.tsv"

    # Doc files
    file_name = "/Users/parvbhullar/Drives/Vault/Projects/Unpod/store-service/test/data/ResumeABHISHEKSINGH.pdf"

    connector = LocalFileConnector(
        file_locations=[file_name], hub_id=22, kn_token="U83Y7PIIL1CICBT6LTVKNXRA"
    )
    # connector.load_credentials({"pdf_password": os.environ["PDF_PASSWORD"]})
    document_batches = connector.load_from_state()
    # print(next(document_batches))
    return document_batches


def get_both_index_names(ref_id) -> tuple[str, str | None]:
    return f"{ref_id}_primary_index", f"{ref_id}_primary_index"


def load_embedder():
    # Need to index for both the primary and secondary index if possible

    org_id = 0
    user_id = 0
    db_session = get_postgres_session()
    db_embedding_model = get_current_db_embedding_model(db_session)
    secondary_db_embedding_model = get_secondary_db_embedding_model(db_session)
    document_index = get_default_document_index(
        primary_index_name=db_embedding_model.index_name,
        secondary_index_name=(
            secondary_db_embedding_model.index_name
            if secondary_db_embedding_model
            else None
        ),
    )

    index_embedding_model = DefaultIndexingEmbedder(
        model_name=db_embedding_model.model_name,
        normalize=db_embedding_model.normalize,
        query_prefix=db_embedding_model.query_prefix,
        passage_prefix=db_embedding_model.passage_prefix,
    )

    print(index_embedding_model)

    indexing_pipeline = build_indexing_pipeline(
        embedder=index_embedding_model,
        document_index=document_index,
        ignore_time_skip=True,
        db_session=db_session,
    )

    documents = use_file_connector()
    for document in documents:
        new_doc, chunks = indexing_pipeline(
            documents=document,
            index_attempt_metadata=IndexAttemptMetadata(
                connector_id=org_id,
                credential_id=user_id,
            ),
        )

        print(new_doc, chunks)


def search_doc(question: AdminSearchRequest):
    query = question.query
    db_session = get_postgres_session()
    embedding_model = get_current_db_embedding_model(db_session)
    document_index = get_default_document_index(
        primary_index_name=embedding_model.index_name, secondary_index_name=None
    )
    final_filters = IndexFilters(
        source_type=question.filters.source_type,
        document_set=question.filters.document_set,
        time_cutoff=question.filters.time_cutoff,
        access_control_list=question.filters.access_control_list,
    )
    matching_chunks = document_index.admin_retrieval(query=query, filters=final_filters)

    documents = chunks_or_sections_to_search_docs(matching_chunks)

    # Deduplicate documents by id
    deduplicated_documents: list[SearchDoc] = []
    seen_documents: set[str] = set()
    for document in documents:
        if document.document_id not in seen_documents:
            deduplicated_documents.append(document)
            seen_documents.add(document.document_id)
    return AdminSearchResponse(documents=deduplicated_documents)


if __name__ == "__main__":
    # import asyncio
    # asyncio.run(main())

    # use_file_connector()
    load_embedder()

    # question = AdminSearchRequest(
    #     query="explain the Progressive Era",
    #     filters=IndexFilters(
    #         source_type=["file"],
    #         document_set=None,
    #         time_cutoff=None,
    #         access_control_list=None,
    #     ),
    # )
    # res = search_doc(question)
    # print(res)

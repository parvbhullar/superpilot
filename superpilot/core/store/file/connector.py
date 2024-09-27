import os
from collections.abc import Iterator
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import IO
import io
from sqlalchemy.orm import Session

from services.store_service.schemas.collection import CollectionFile
from services.store_service.views.collection import get_collection
from super_store.db_store.mongo import MongoStore
from super_store.processor import StoreProcessor
from super_store.schema import SchemaCreator
from super_store.configs.app_configs import INDEX_BATCH_SIZE
from super_store.configs.constants import DocumentSource
from super_store.connectors.cross_connector_utils.miscellaneous_utils import time_str_to_utc
from super_store.connectors.interfaces import GenerateDocumentsOutput
from super_store.connectors.interfaces import LoadConnector
from super_store.connectors.models import BasicExpertInfo
from super_store.connectors.models import Document
from super_store.connectors.models import Section
from super_store.db.engine import get_sqlalchemy_engine
from super_store.file_processing.extract_file_text import check_file_ext_is_valid, \
    is_tabular_file_extension
from super_store.file_processing.extract_file_text import detect_encoding
from super_store.file_processing.extract_file_text import extract_file_text
from super_store.file_processing.extract_file_text import get_file_ext
from super_store.file_processing.extract_file_text import is_text_file_extension
from super_store.file_processing.extract_file_text import load_files_from_zip
from super_store.file_processing.extract_file_text import pdf_to_text
from super_store.file_processing.extract_file_text import read_text_file
from super_store.file_processing.extract_tabular_text import read_tabular_file
from super_store.utils.logger import setup_logger
from services.store_service.core.string import string_to_int

logger = setup_logger()


def read_file_as_bytes(file_name):
    if not file_name.startswith("http") and not file_name.startswith("file"):
        file_name = f"file://{file_name}"
    collection_obj = CollectionFile(url=file_name)
    fileObj = collection_obj.load()
    if not fileObj:
        return {
            "data": {"error": f"�� File not found at {file_name}"},
            "success": False,
        }
    return fileObj


def _read_files_and_metadata(
    file_name: str,
    config: dict[str, Any] = {},
) -> Iterator[tuple[str, IO, dict[str, Any]]]:
    """Reads the file into IO, in the case of a zip file, yields each individual
    file contained within, also includes the metadata dict if packaged in the zip"""
    extension = get_file_ext(file_name)
    metadata: dict[str, Any] = {}
    directory_path = os.path.dirname(file_name)

    # file_content = get_default_file_store(db_session).read_file(file_name, mode="b")
    file_content = read_file_as_bytes(file_name)

    if extension == ".zip":
        for file_info, file, metadata in load_files_from_zip(
            file_content, ignore_dirs=True
        ):
            push_to_mongo(config, os.path.join(directory_path, file_info.filename))
            yield os.path.join(directory_path, file_info.filename), file, metadata
    elif is_tabular_file_extension(file_name):
        push_to_mongo(config, os.path.join(directory_path, file_name))
        #  return each records as a file content
        for file_content, metadata in read_tabular_file(file_name):
            yield f"{str(string_to_int(file_content, len=16))}__{os.path.basename(file_name)}", bytes(file_content, "utf-8"), metadata

    elif check_file_ext_is_valid(extension):
        push_to_mongo(config, os.path.join(directory_path, file_name))
        yield file_name, file_content, metadata
    else:
        logger.warning(f"Skipping file '{file_name}' with extension '{extension}'")


async def push_to_mongo(config, file_path):
    try:
        collection_id = get_collection(config)
        db_manager = MongoStore(collection=collection_id)
        processor = StoreProcessor(db_manager)
        res = await processor.process(
            file_path, collection_id, save_log=True, token=config.get("token", ""), index=True, config=config
        )
        logger.warning(f"Pushing data to mongodb as well, collection_id: {collection_id}")
    except Exception as e:
        logger.error(f"Error while pushing data to mongodb: {e}")


def _process_file(
    file_name: str,
    file: IO[Any],
    metadata: dict[str, Any] | None = None,
    pdf_pass: str | None = None,
    *args, **kwargs
) -> list[Document]:
    document_id = kwargs.get("document_id", None)
    extension = get_file_ext(file_name)
    if not check_file_ext_is_valid(extension):
        logger.warning(f"Skipping file '{file_name}' with extension '{extension}'")
        return []

    file_metadata: dict[str, Any] = {}

    if is_text_file_extension(file_name):
        encoding = detect_encoding(file)
        file_content_raw, file_metadata = read_text_file(
            file, encoding=encoding, ignore_unpod_metadata=False
        )
    elif is_tabular_file_extension(file_name):
        # In case of tabular file, we just need to pass file content and metadata recevied from previous method
        file_content_raw = file
        file_metadata = metadata
    # Using the PDF reader function directly to pass in passsword cleanly
    elif extension == ".pdf":
        # file_content_raw = pdf_to_text(file=file, pdf_pass=pdf_pass)
        file_content_raw = file
        file_metadata = metadata

    else:
        file_content_raw = extract_file_text(
            file_name=file_name,
            file=file,
        )

    all_metadata = {**metadata, **file_metadata} if metadata else file_metadata

    # If this is set, we will show this in the UI as the "name" of the file
    file_display_name = all_metadata.get("file_display_name") or os.path.basename(
        file_name
    )
    title = (
        all_metadata["title"] or "" if "title" in all_metadata else file_display_name
    )

    time_updated = all_metadata.get("time_updated", datetime.now(timezone.utc))
    if isinstance(time_updated, str):
        time_updated = time_str_to_utc(time_updated)

    dt_str = all_metadata.get("doc_updated_at")
    final_time_updated = time_str_to_utc(dt_str) if dt_str else time_updated

    # Metadata tags separate from the Unpod specific fields
    metadata_tags = {
        k: v if isinstance(v, (list, str)) else str(v)
        for k, v in all_metadata.items()
        if k
        not in [
            "time_updated",
            "doc_updated_at",
            "link",
            "primary_owners",
            "secondary_owners",
            "filename",
            "file_display_name",
            "title",
        ]
    }

    p_owner_names = all_metadata.get("primary_owners")
    s_owner_names = all_metadata.get("secondary_owners")
    p_owners = (
        [BasicExpertInfo(display_name=name) for name in p_owner_names]
        if p_owner_names
        else None
    )
    s_owners = (
        [BasicExpertInfo(display_name=name) for name in s_owner_names]
        if s_owner_names
        else None
    )

    return [
        Document(
            id=f"FILE_CONNECTOR__{file_name if document_id is None else document_id}",  # add a prefix to avoid conflicts with other connectors
            sections=[
                Section(link=all_metadata.get("link"), text=file_content_raw.strip())
            ],
            source=DocumentSource.FILE,
            semantic_identifier=file_display_name,
            title=title,
            doc_updated_at=final_time_updated,
            primary_owners=p_owners,
            secondary_owners=s_owners,
            # currently metadata just houses tags, other stuff like owners / updated at have dedicated fields
            metadata=metadata_tags,
            hub_id=str(kwargs.get("hub_id")) if kwargs.get("hub_id") else None,
            kn_token=str(kwargs.get("kn_token")) if kwargs.get("kn_token") else None,
        )
    ]


class LocalFileConnector(LoadConnector):
    def __init__(
        self,
        file_locations: list[Path | str],
        batch_size: int = INDEX_BATCH_SIZE,
        *args, **kwargs
    ) -> None:
        self.file_locations = [Path(file_location) for file_location in file_locations]
        self.batch_size = batch_size
        self.pdf_pass: str | None = None
        self.kwargs = kwargs

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        self.pdf_pass = credentials.get("pdf_password")
        return None

    def load_from_state(self) -> GenerateDocumentsOutput:
        documents: list[Document] = []
        for file_path in self.file_locations:
            current_datetime = datetime.now(timezone.utc)
            files = _read_files_and_metadata(
                file_name=str(file_path)
            )

            for file_name, file, metadata in files:
                metadata["time_updated"] = metadata.get(
                    "time_updated", current_datetime
                )
                documents.extend(
                    _process_file(file_name, file, metadata, self.pdf_pass, **self.kwargs)
                )

                if len(documents) >= self.batch_size:
                    yield documents
                    documents = []

            if documents:
                yield documents




if __name__ == "__main__":
    # file_name =
    connector = LocalFileConnector(file_locations=[os.environ["TEST_FILE"]])
    connector.load_credentials({"pdf_password": os.environ["PDF_PASSWORD"]})

    document_batches = connector.load_from_state()
    print(next(document_batches))

from typing import IO, Any
from superpilot.core.store.file.models import Document as SuperPilotDocument
from superpilot.core.store.file_processing.extract_file_text import (
    pdf_to_text,
    check_file_ext_is_valid,
    detect_encoding,
    extract_file_text,
    get_file_ext,
    is_text_file_extension,
    read_text_file
)
from superpilot.core.logging.logging import setup_logger
from superpilot.core.store.file.models import BasicExpertInfo
from superpilot.core.store.vectorstore.vespa.configs.constants import DocumentSource
from unstructured.partition.auto import partition
#from superpilot.core.memory.vespa_memory import extract_metadata
from datetime import datetime, timezone
import PyPDF2
import os

logger = setup_logger()

class Document:
    """Custom Document class to hold unstructured elements and markdown content."""
    def __init__(self, id: str, elements: list, markdown: str, **kwargs):
        self.id = id
        self.elements = elements
        self.markdown = markdown  # New attribute for markdown content
        self.source = kwargs.get('source', DocumentSource.FILE)
        self.semantic_identifier = kwargs.get('semantic_identifier')
        self.title = kwargs.get('title')
        self.doc_updated_at = kwargs.get('doc_updated_at')
        self.primary_owners = kwargs.get('primary_owners')
        self.secondary_owners = kwargs.get('secondary_owners')
        self.metadata = kwargs.get('metadata')
        self.hub_id = kwargs.get('hub_id')
        self.kn_token = kwargs.get('kn_token')



from datetime import datetime,timezone
def time_str_to_utc(time_str: str) -> datetime:
    """
    Convert a time string to a UTC datetime object.

    Args:
        time_str (str): The time string to convert.

    Returns:
        datetime: A UTC datetime object.
    """
    # Define the possible formats for the input time string
    formats = [
        "%Y-%m-%d %H:%M:%S",  # e.g., "2024-10-10 14:30:00"
        "%Y-%m-%dT%H:%M:%S",  # e.g., "2024-10-10T14:30:00"
        "%Y/%m/%d %H:%M:%S",  # e.g., "2024/10/10 14:30:00"
        "%d-%m-%Y %H:%M:%S",  # e.g., "10-10-2024 14:30:00"
        "%d/%m/%Y %H:%M:%S",  # e.g., "10/10/2024 14:30:00"
        "%Y-%m-%d %H:%M",     # e.g., "2024-10-10 14:30"
        "%Y-%m-%d",           # e.g., "2024-10-10"
    ]

    for fmt in formats:
        try:
            # Parse the time string into a naive datetime object
            naive_dt = datetime.strptime(time_str, fmt)
            # Convert naive datetime to UTC
            return naive_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    raise ValueError(f"Time string '{time_str}' is not in a recognized format.")


def extract_metadata(file_path):
    """
    Extract metadata from the file such as file size, creation date, last modified date,
    and, for PDFs, the number of pages.
    """
    metadata = {
        "file_name": os.path.basename(file_path),
        "file_size": str(os.path.getsize(file_path)),  # Convert file size to string
        "file_path": file_path,
        "creation_date": datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
        "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # If the file is a PDF, we can also extract the number of pages
    if file_path.lower().endswith('.pdf'):
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadata["num_pages"] = str(len(reader.pages))  # Convert number of pages to string
        except Exception as e:
            metadata["num_pages"] = "Error reading PDF: " + str(e)
    
    return metadata
def _process_file(
    file_name: str,
    file: IO[Any],
    metadata: dict[str, Any] | None = None,
    pdf_pass: str | None = None,
    *args, **kwargs
) -> Document:
    document_id = kwargs.get("document_id", None)
    extension = get_file_ext(file)
    elements = partition(filename=file)
    
    if not check_file_ext_is_valid(extension):
        logger.warning(f"Skipping file '{file_name}' with extension '{extension}'")
        return None  # Return None if the file extension is not valid

    file_metadata: dict[str, Any] = {}
    file_content_raw = ""

    if is_text_file_extension(file):
        encoding = detect_encoding(file)
        file_content_raw, file_metadata = read_text_file(
            file, encoding=encoding, ignore_unpod_metadata=False
        )
    elif extension == ".pdf":
        # For PDF files, process the text using unstructured library
        elements = partition(filename=file)  # Use unstructured to partition the PDF
        file_content_raw = pdf_to_text(file=file, pdf_pass=pdf_pass)
        file_metadata = metadata
    else:
        file_content_raw = extract_file_text(
            file_name=file_name,
            file=file,
        )

    all_metadata = {**metadata, **file_metadata} if metadata else file_metadata
    if all_metadata is None:
        all_metadata = {}
        
    logger.info(f"Extracted Metadata for {file_name}: {all_metadata}")

    # Extract file metadata and assign default values
    file_display_name = all_metadata.get("file_display_name") or os.path.basename(file_name)
    title = all_metadata.get("title") or file_display_name

    time_updated = all_metadata.get("time_updated", datetime.now(timezone.utc))
    
    if isinstance(time_updated, str):
        time_updated = time_str_to_utc(time_updated)

    dt_str = all_metadata.get("doc_updated_at")
    final_time_updated = time_str_to_utc(dt_str) if dt_str else time_updated

    metadata_tags = {
        k: v if isinstance(v, (list, str)) else str(v)
        for k, v in all_metadata.items()
        if k not in [
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

    # Construct and return the Document object with unstructured elements and markdown content
    extracted_metadata = extract_metadata(file)

    document = Document(
        id=f"FILE_CONNECTOR__{file_name if document_id is None else document_id}",  
        elements=elements,  # Use elements from unstructured library instead of sections
        markdown=str(file_content_raw),  # Add markdown content from file_content_raw
        source=DocumentSource.FILE,
        semantic_identifier=file_display_name,
        title=title,
        doc_updated_at=final_time_updated,
        primary_owners=p_owners,
        secondary_owners=s_owners,
        metadata=extracted_metadata,
        hub_id=str(kwargs.get("hub_id")) if kwargs.get("hub_id") else None,
        kn_token=str(kwargs.get("kn_token")) if kwargs.get("kn_token") else None,
    )

    return document

# Example usage (if needed)
# with open('example-docs/pdf/layout-parser-paper-fast.pdf', 'rb') as f:
#     doc = _process_file('layout-parser-paper-fast.pdf', f)
import sys
import os
import time
import json
import re
import numpy as np
import asyncio
from itertools import chain
from pathlib import Path
from datetime import datetime, timezone
from PyPDF2 import PdfReader
from typing import Any, IO, Dict, List


# Adjust the path to import from the superpilot package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
print(sys.path[0])
from superpilot.core.store.schema import Object
# Import necessary modules from superpilot
from superpilot.core.store.file_processing.extract_file_text import (
    pdf_to_text,
    detect_encoding,
    read_text_file,
    extract_file_text,
    get_file_ext,
    check_file_ext_is_valid,
    is_text_file_extension,
)
from superpilot.core.store.file.models import Document, Section, BasicExpertInfo
from superpilot.core.store.indexing.models import DocAwareChunk
from superpilot.core.store.indexing.chunker import DefaultChunker
from superpilot.core.store.vectorstore.vespa.configs.constants import DocumentSource

from superpilot.core.store.vectorstore.vespa.base import VespaStore
from superpilot.core.logging.logging import setup_logger

logger = setup_logger()

def get_first_sentence(content: str) -> str:
    """Extracts the first sentence from the content."""
    sentence = re.split(r'[.!?]', content)[0].strip()
    return sentence if sentence else content

def remove_duplicates(object_list: List[Any]) -> List[Any]:
    """Removes duplicate objects based on their content."""
    unique_objects = []
    seen_contents = set()
    
    for obj in object_list:
        if obj.content not in seen_contents:
            unique_objects.append(obj)
            seen_contents.add(obj.content)
    
    return unique_objects

def extract_metadata(file: IO[Any]) -> Dict[str, str]:
    """Extracts metadata from the provided PDF file."""
    metadata = {}
    
    # Dummy data initialization
    dummy_data = {
        "user_name": "John Doe",
        "user_id": "123",
        "file_path": "/path/to/your/pdf_file.pdf",
        "space_id": "space_001",
        "organization": "My Organization",
        "_id": "file_001",
        "file_upload_date": str(datetime.now(timezone.utc)),
    }

    # Read the PDF file for metadata extraction
    reader = PdfReader(file)
    info = reader.metadata
    
    # Merge dummy data into metadata
    metadata.update(dummy_data)
    
    if info:
        metadata.update({key: str(info[key]) for key in info if key})
    
    return metadata

def generate_embeddings(text: str) -> dict:
    """Generates random embeddings for the given text."""
    return np.random.rand(300).tolist()

def _process_file(file_name: str, file: IO[Any], metadata: dict[str, Any] | None = None) -> Document:
    """Processes the input file and extracts its content and metadata."""
    
    extension = get_file_ext(file_name)
    
    if not check_file_ext_is_valid(extension):
        logger.warning(f"Skipping file '{file_name}' with extension '{extension}'")
        return None  # Return None if the file extension is not valid
    
    file_metadata: dict[str, Any] = {}
    
    if is_text_file_extension(file_name):
        encoding = detect_encoding(file)
        file_content_raw, file_metadata = read_text_file(file, encoding=encoding)
    
    elif extension == ".pdf":
        file_content_raw = pdf_to_text(file=file)
        file_metadata = metadata or {}
    
    else:
        file_content_raw = extract_file_text(file_name=file_name, file=file)
    
    # Extract and prepare all metadata for Document creation
    all_metadata = {**metadata, **file_metadata} if metadata else file_metadata
    
    # Extract relevant fields from metadata
    file_display_name = all_metadata.get("file_display_name") or os.path.basename(file_name)
    
    document = Document(
        id=f"FILE_CONNECTOR__{file_name}",
        sections=[Section(link=all_metadata.get("link"), text=file_content_raw.strip())],
        source=DocumentSource.FILE,
        semantic_identifier=file_display_name,
        title=all_metadata.get("title", file_display_name),
        doc_updated_at=datetime.now(timezone.utc),
        primary_owners=[BasicExpertInfo(display_name=name) for name in all_metadata.get("primary_owners", [])],
        secondary_owners=[BasicExpertInfo(display_name=name) for name in all_metadata.get("secondary_owners", [])],
        metadata=extract_metadata(file),
        hub_id=str(metadata.get("hub_id")) if metadata else None,
        kn_token=str(metadata.get("kn_token")) if metadata else None,
    )
    
    return document

async def process_document(file_path: str) -> List[Dict]:
    """Main function to process the input file and return indexed objects."""
    
    file_name = os.path.basename(file_path)

    # Process the input document based on its type (PDF/Text/JSON)
    with open(file_path, "rb") as input_file:
        document = _process_file(file_name=file_name, file=input_file)

        # Chunking process for the document
        chunker = DefaultChunker()
        chunks: List[DocAwareChunk] = list(chain(*[chunker.chunk(document=document) for _ in range(10)]))
        
        object_list = []
        
        for i, chunk in enumerate(chunks):
            first_sentence = get_first_sentence(chunk.content)
            obj = Object(
                blurb=first_sentence,
                ref_id=document.id,
                obj_id=str(i),
                content=chunk.content,
                source=file_name,
                privacy='public',
                embeddings={"embedding": generate_embeddings(chunk.content)},
                metadata=extract_metadata(input_file),
                type='text'
            )
            object_list.append(obj)

        object_list = remove_duplicates(object_list)

        vespa_store = VespaStore(index_name="sample_index",secondary_index_name=None)
        indexed_objects = vespa_store.index(chunks=object_list)

        return indexed_objects
    

# Function to call from other modules/scripts with a specific file path.
async def call_main_function(file_path: str) -> List[Dict]:
    """Calls the main processing function with a given file path."""
    return await process_document(file_path)



if __name__ == "__main__":
    # Example usage with a PDF or text file path.
    pdf_file_path = 'tests/test_file.pdf'  # Change this to your actual file path.
    
    indexed_objects_result = asyncio.run(main(pdf_file_path))
    
    print("Number of indexed objects:", len(indexed_objects_result))
import sys
import logging
import os
import time
from itertools import chain
import asyncio

import os
from collections.abc import Iterator
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import IO
import io
# from sqlalchemy.orm import Session

# Adjust the path to import from the superpilot package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
#print(sys.path[0])
# Import necessary modules from superpilot
# from superpilot.core.store.file_processing.extract_file_text import pdf_to_text
from superpilot.core.store.file_processing.extract_file_text import pdf_to_text
#from superpilot.core.store.file.connector import _process_file
from superpilot.core.store.file.models import Document, Section
from superpilot.core.store.indexing.models import DocAwareChunk
from superpilot.core.store.indexing.chunker import DefaultChunker
from superpilot.core.store.schema import Object
from superpilot.core.store.vectorstore.vespa.base import VespaStore
from superpilot.core.store.file.models import BasicExpertInfo,Document,Section

# Assuming this is a helper function from your project
#from test_chunker import toDocument  # Adjust if the test_chunker has other relevant imports


from superpilot.core.store.file_processing.extract_file_text import check_file_ext_is_valid #is_perpilot.core.store.le_extension
from superpilot.core.store.file_processing.extract_file_text import detect_encoding
from superpilot.core.store.file_processing.extract_file_text import extract_file_text
from superpilot.core.store.file_processing.extract_file_text import get_file_ext
from superpilot.core.store.file_processing.extract_file_text import is_text_file_extension,is_tabular_file_extension
from superpilot.core.store.file_processing.extract_file_text import load_files_from_zip
from superpilot.core.store.file_processing.extract_file_text import pdf_to_text
from superpilot.core.store.file_processing.extract_file_text import read_text_file
#from superpilot.core.store.file_processing.extract_tabular_text import read_tabular_file
from superpilot.core.logging.logging import setup_logger
from superpilot.core.store.vectorstore.vespa.configs.constants import DocumentSource

#from super_store.connectors.cross_connector_utils.miscellaneous_utils import time_str_to_utcx

logger = setup_logger()

def _process_file(
    file_name: str,
    file: IO[Any],
    metadata: dict[str, Any] | None = None,
    pdf_pass: str | None = None,
    *args, **kwargs
) -> Document:
    document_id = kwargs.get("document_id", None)
    extension = get_file_ext(file_name)
    if not check_file_ext_is_valid(extension):
        logger.warning(f"Skipping file '{file_name}' with extension '{extension}'")
        return None  # Return None if the file extension is not valid

    file_metadata: dict[str, Any] = {}

    if is_text_file_extension(file_name):
        encoding = detect_encoding(file)
        file_content_raw, file_metadata = read_text_file(
            file, encoding=encoding, ignore_unpod_metadata=False
        )
    elif extension == ".pdf":
        # For PDF files, process the text
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

    # Construct and return the Document object
    document = Document(
        id=f"FILE_CONNECTOR__{file_name if document_id is None else document_id}",  # Document ID
        sections=[Section(link=all_metadata.get("link"), text=file_content_raw.strip())],
        source=DocumentSource.FILE,
        semantic_identifier=file_display_name,
        title=title,
        doc_updated_at=final_time_updated,
        primary_owners=p_owners,
        secondary_owners=s_owners,
        metadata=metadata_tags,
        hub_id=str(kwargs.get("hub_id")) if kwargs.get("hub_id") else None,
        kn_token=str(kwargs.get("kn_token")) if kwargs.get("kn_token") else None,
    )

    return document  # Return a single Document object





async def main():
    pdf_file_path = "/Users/zestgeek-29/Desktop/Work/superpilot/superpilot/tests/final_data-and-ai-governance.6sept2023.pdf"
    file_name = os.path.basename(pdf_file_path)

    # Process the PDF document
    with open(pdf_file_path, "rb") as pdf_file:
        document = _process_file(file_name=file_name, file=pdf_file, pdf_pass=None)

    # Initialize the chunker and start chunking the document
    print("Document Type:",type(document))
    chunker = DefaultChunker()
    t1 = time.time()
    chunks: list[DocAwareChunk] = list(
        chain(*[chunker.chunk(document=document) for _ in range(10)])
    )
    print(f"Number of chunks: {len(chunks)}")
    
    # for ch in chunks:
        # print(str(ch) + "\n")

    t2 = time.time()
    print("Time Taken", round(t2 - t1))
    blurb='blurb'
    # Create Object class instances from chunks
    object_list = []
    for i, chunk in enumerate(chunks):
        obj = Object(
            blurb=blurb,
            id=f"{document.id}_{i}",  # Unique object ID
            ref_id=document.id,       # Document reference ID
            obj_id=str(i),                 # Chunk index as object ID
            content=chunk.content, 
            source='path', 
            privacy='public',
            embeddings={},
            metadata= {},
            type='text' # Set chunk content
        )
        object_list.append(obj)

    # Print the list of Object instances
    # for obj in object_list:
        # print(obj)
    print("Number of chunks:",len(object_list))

    content_list = [str(obj.content) for obj in object_list]

    def word_count(sentences):
        word_counts = [len(sentence.split()) for sentence in sentences]  # Count words in each sentence
        total_words = sum(word_counts)  # Sum the word counts
        average_words = total_words / len(sentences) if sentences else 0  # Compute average, handling empty list case
        return average_words
    average_words=word_count(content_list)
    print("Average Words of Chunks",average_words)


    
    # Initialize the VespaStore and index the objects
    vespa_store = VespaStore(index_name="sample_index", secondary_index_name=None)
    indexed_objects = vespa_store.index(chunks=object_list)
    print("Number of indexed objects:",len(indexed_objects))
    print("indexed objects:",indexed_objects)
    

    # Print the final indexed objects
    

if __name__ == "__main__":
    asyncio.run(main())

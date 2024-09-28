import sys
import logging
import os
import time
from itertools import chain
import asyncio

# Adjust the path to import from the superpilot package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
#print(sys.path[0])
# Import necessary modules from superpilot
#from superpilot.core.store.file_processing.extract_file_text import pdf_to_text
from superpilot.core.store.file_processing.extract_file_text import pdf_to_text
from superpilot.core.store.file.connector import _process_file
from superpilot.core.store.file.models import Document, Section
from superpilot.core.store.indexing.models import DocAwareChunk
from superpilot.core.store.indexing.chunker import DefaultChunker
from superpilot.core.store.schema import Object
from superpilot.core.store.vectorstore.vespa.base import VespaStore

# Assuming this is a helper function from your project
from test_chunker import toDocument  # Adjust if the test_chunker has other relevant imports

async def main():
    pdf_file_path = "superpilot/tests/final_data-and-ai-governance.6sept2023.pdf"
    file_name = os.path.basename(pdf_file_path)

    # Extract text from the PDF
    text = pdf_to_text(pdf_file_path)

    # Process the PDF document
    document = _process_file(file_name=file_name, file=open(pdf_file_path, "rb"), pdf_pass=None)

    # Initialize the chunker and start chunking the document
    chunker = DefaultChunker()
    t1 = time.time()
    chunks: list[DocAwareChunk] = list(
        chain(*[chunker.chunk(document=document) for _ in range(10)])  # Assuming chunking 10 times
    )
    print(f"Number of chunks: {len(chunks)}")
    
    for ch in chunks:
        print(str(ch) + "\n")

    t2 = time.time()
    print("Time Taken", round(t2 - t1))

    # Create Object class instances from chunks
    object_list = []
    for i, chunk in enumerate(chunks):
        obj = Object(
            id=f"{document.id}_{i}",  # Unique object ID
            ref_id=document.id,       # Document reference ID
            obj_id=i,                 # Chunk index as object ID
            content=chunk.content     # Set chunk content
        )
        object_list.append(obj)

    # Print the list of Object instances
    for obj in object_list:
        print(obj)

    # Initialize the VespaStore and index the objects
    vespa_store = VespaStore(index_name="sample_index", secondary_index_name=None)
    indexed_objects = vespa_store.index(chunks=object_list)

    # Print the final indexed objects
    print("Final indexed objects:")
    for obj in indexed_objects:
        print(obj)

if __name__ == "__main__":
    asyncio.run(main())

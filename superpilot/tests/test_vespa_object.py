import sys
import os
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.store.vectorstore.vespa.vespa_file_index import call_main_function
from superpilot.core.store.search.retrieval.query_escalator import *
from superpilot.core.store.search.retrieval.search_runner import query_processing
from superpilot.core.memory.vespa_memory import MemoryManager

vespa_url='http://localhost:8081/'
memory=MemoryManager(store_url=vespa_url,ref_id='test_memory')

file_path=input('File path:')

memory.add_memory(input_data=file_path)
print('Added to memory')

query_string = input('Enter Query: ')
query_string = query_processing(query_string)



filter_dict = {}

top_chunks=search(query=query_string,filters=filter_dict)

print(top_chunks)


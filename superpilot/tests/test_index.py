import sys
import os
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.store.vectorstore.vespa.vespa_file_index import call_main_function
from superpilot.core.memory.vespa_memory import MemoryManager
#from vespa.application import Vespa





# Define the filze path for the PDF file
file_path = '/Users/zestgeek-29/Desktop/Work/superpilot/superpilot/tests/test_file.pdf'


    # Call the main function to get results from the PDF file
#results =call_main_function(file_path=file_path)

#print(type(results))
vespa_url='http://localhost:8081/document/v1/'
memory=MemoryManager(store_url=vespa_url,ref_id='test_memory')
#memory.add_memory2(input_data=file_path)
memory.add_memory(input_data=file_path)

    # Initialize the Vespa application connection




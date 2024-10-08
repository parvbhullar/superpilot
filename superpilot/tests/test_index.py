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


import os

def add_all_files_to_memory(folder_path):
    # Loop through all files in the folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)  # Get the full file path
            # Assuming memory.add_memory() takes file path as input
            memory.add_memory(input_data=file_path)
            print(f"Added to memory: {file_path}")

# Specify the folder where the files are stored
folder_path = '/Users/zestgeek-29/Desktop/Work/samples'

# Call the function
add_all_files_to_memory(folder_path)



#memory.add_memory2(input_data=file_path)
'''
memory.add_memory(input_data=file_path)
print("Added")
print()
print()
print("Retrieved")
print(memory.get_memory('test_file_1_2'))
#chunks=memory.get_all_memory()
#c=1
#for chunk in chunks:
    #print(c,chunk.content)
    #c=c+1

#print(memory.get_all_doc_ids())
'''
    # Initialize the Vespa application connection




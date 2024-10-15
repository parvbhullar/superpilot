import sys
import os
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.store.vectorstore.vespa.vespa_file_index import call_main_function
from superpilot.core.store.search.retrieval.query_escalator import *
from superpilot.core.store.search.retrieval.search_runner import query_processing
from superpilot.core.memory.vespa_memory import MemoryManager

#vespa_url='https://fb73ae7d.baed2213.z.vespa-app.cloud/'
vespa_url='http://localhost:8081/'
memory=MemoryManager(store_url=vespa_url,ref_id='test_memory')

#file_path=input('File path:')

file_path='/Users/zestgeek-29/Desktop/Work/samples/document7.pdf'



document=memory.ingest(source=file_path,ingest_type='file_path',ingest_config={},save=True)
print(document)

memory.add_memory(document)
#memory.add_memory(document)
# print("Objects created")
# object=memory.process_document(document)
# for obj in object:
#     if len(str(obj.content).split())>50:
#         print("Content",obj.content,"Object Id",obj.obj_id)
#         print()
# print('Data Added') 

query_string = input('Enter Query: ')
query_string = query_processing(query_string)

filter_dict = {}



top_chunks=memory.search(query=query_string,filters=filter_dict)
if len(top_chunks)>0:

        printed_ids=set()
        for obj in top_chunks:
                if obj.obj_id not in printed_ids:  # Check if the obj_id has not been printed
                        print(f"- {obj.obj_id}")  # Print the obj_id
                        printed_ids.add(obj.obj_id)

else:

        print('No Matches Found')




import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.core.store.search.retrieval.query_escalator import *
from superpilot.core.store.search.retrieval.search_runner import query_processing
from superpilot.core.memory.vespa_memory import MemoryManager


'''
    # Sample chunks (objects) for testing
vespa_url = 'http://localhost:8081/document/v1/'
memory = MemoryManager(store_url=vespa_url, ref_id='test_memory')
chunks = memory.get_all_memory()

# Display all chunks
c = 1
print('All chunks:')
# for chunk in chunks:
#     print(c, chunk.obj_id)
#     c += 1
#     print()
if len(chunks)>0:

# Input query string
    query_string = input('Enter Query: ')
    query_string = query_processing(query_string)
    #keywords=generate_keywords_and_sentences(query_string)
    #print('Keywords: ',keywords)
    # print('Sentences: ',sentences)

    # Generate keywords from the query string
    #query_keywords = generate_keywords(query_string)
    # Precompute object embeddings
    #object_embeddings = preprocess_objects(chunks)
    # Retrieve related objects based on the generated keywords


    top_chunks = retrieve_objects(objects=chunks, query=query_string)
    # Display results
    printed_ids = set()  # Create a set to track printed obj_ids

    for obj in top_chunks:
        if obj.obj_id not in printed_ids:  # Check if the obj_id has not been printed
            print(f"- {obj.obj_id}")  # Print the obj_id
            printed_ids.add(obj.obj_id)

else:
    print('Cant Fetch Objects')



vespa_url = 'http://localhost:8081/document/v1/'
memory = MemoryManager(store_url=vespa_url, ref_id='test_memory')
chunks = memory.get_all_memory()

print('Chunks Loaded')

if len(chunks) >0:

#Search Implementations
    query_string = input('Enter Query: ')
    query_string = query_processing(query_string)

    filter_dict = {
        'blurb': 'Artificial Intelligence'
    }

    top_chunks=search_objects(objects=chunks,query=query_string, filter_dict=filter_dict)
    print('Number of top chunks with filtering',len(top_chunks))
    printed_ids=set()
    for obj in top_chunks:
            if obj.obj_id not in printed_ids:  # Check if the obj_id has not been printed
                print(f"- {obj.obj_id}")  # Print the obj_id
                printed_ids.add(obj.obj_id)

#Quantum Computing and Artificial Intelligence
else:
     print('No chunks found')
'''

query_string = input('Enter Query: ')
query_string = query_processing(query_string)

filter_dict = {}

#top_chunks=search(query=query_string,filters=filter_dict)
top_chunks=search_objects(query=query_string,filters=filter_dict)
#

printed_ids=set()
for obj in top_chunks:
            if obj.obj_id not in printed_ids:  # Check if the obj_id has not been printed
                print(f"- {obj.obj_id}")  # Print the obj_id
                printed_ids.add(obj.obj_id)
#print(top_chunks)


print('Query Done')
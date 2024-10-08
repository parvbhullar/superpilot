import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.core.store.search.retrieval.query_escalator import *
from superpilot.core.store.search.retrieval.search_runner import query_processing
from superpilot.core.memory.vespa_memory import MemoryManager


def main():
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
    
    # Input query string
    query_string = input('Enter Query: ')
    query_string = query_processing(query_string)
    
    # Generate keywords from the query string
    #query_keywords = generate_keywords(query_string)

    # Precompute object embeddings
    #object_embeddings = preprocess_objects(chunks)

    # Retrieve related objects based on the generated keywords
    top_chunks = retrieve_related_objects(objects=chunks, query=query_string)

    # Display results
    print("\nTop Related Chunks:")
    for obj in top_chunks:
        print(f"- {obj.obj_id}")


if __name__ == "__main__":
    main()

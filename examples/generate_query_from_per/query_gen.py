import os
import openai
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# openai.api_key = "your_actual_api_key_here"



def load_index(directory_path):
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist.")
        return None

    files = os.listdir(directory_path)
    print(f"Files in {directory_path}: {files}")  

    documents = SimpleDirectoryReader(directory_path).load_data()
    index = VectorStoreIndex.from_documents(documents)
    return index

def main():
    directory_path = "superpilot/examples/generate_query_from_per/persona_output.jsonl"  
    index = load_index(directory_path)

    if index is None:
        print("Failed to load index. Exiting.")
        return

    query_engine = index.as_query_engine()

    print("Welcome to the Llama Index Query Agent! Type 'exit' to stop.")
    while True:
        user_query = input("You: ")
        
        if user_query.lower() == 'exit':
            print("Goodbye!")
            break
        
        response = query_engine.query(user_query)
        
        print(f"Response: {response}")

if __name__ == "__main__":
    main()


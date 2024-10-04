
from superpilot.core.store.schema import Object

import requests
import time
import json
from typing import List, Union
import asyncio
from superpilot.core.store.vectorstore.vespa.vespa_file_index import call_main_function
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import Timeout, ConnectionError

#vespa_url="http://localhost:8080/document/v1/<namespace>/<document-type>/"


import numpy as np

def truncation(embedding, chunk_size=100):
    """Truncate the embedding into chunks of specified size."""
    # Ensure embedding is a NumPy array
    embedding_array = np.array(embedding)

    # Check if the length of the embedding is exactly 300
    if len(embedding_array) != 300:
        raise ValueError("Embedding must be of length 300.")

    # Split into chunks of 100 elements each
    chunks = [embedding_array[i:i + chunk_size].tolist() for i in range(0, len(embedding_array), chunk_size)]
    
    # Ensure we have exactly 3 chunks
    if len(chunks) != 3:
        raise ValueError("Unexpected number of chunks created. Expected 3 chunks of size 100.")
    
    return chunks

class MemoryManager:
    def __init__(self, store_url: str, ref_id: str, schema_name: str=None):
        self.store_url = store_url
        self.ref_id = ref_id
        self.schema_name =  schema_name or "object_schema"

    
    def convert_to_objects(self,input_data: Union[str, dict]):
        results=asyncio.run(call_main_function(input_data))
        return(results)
    
    def to_dict(self,obj):
        """Converts an Object type to a dictionary."""
        
        return {
            "fields":{
            "blurb": obj.blurb,
            "ref_id": obj.ref_id,
            "obj_id": obj.obj_id,
            "content": obj.content,
            "source": obj.source,
            "privacy": obj.privacy,
            "embeddings": obj.embeddings,
            #"embeddings": truncation(obj),
            #"embeddings2": obj.embeddings['embedding'][101:200],
            #"embeddings3": obj.embeddings['embedding'][201:300],
            "metadata": [
                f"user_name: {obj.metadata['user_name']}",
                f"user_id: {obj.metadata['user_id']}",
                f"file_path: {obj.metadata['file_path']}",
                f"space_id: {obj.metadata['space_id']}",
                f"organization: {obj.metadata['organization']}",
                f"_id: {obj.metadata['_id']}",
                f"file_upload_date: {obj.metadata['file_upload_date']}"
            ],
            "type": obj.type
            }
        }
    
    
    

    
        

    def add_memory(self, input_data):
        """Add memory to Vespa AI engine."""
        results = self.convert_to_objects(input_data)
        print('Result Type', type(results))
        
        max_retries = 5
        retry_delay = 2
        namespace = "testing"
        document_type = "unpod_chunk"
        
        url = self.store_url + f'{self.schema_name}/{self.schema_name}/docid/'
        print('Url', url)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer YOUR_ACCESS_TOKEN'  # Replace with your actual access token if required
        }       

        # Retry logic for sending POST requests to Vespa
        for cluster_id, cluster in results.items():
            for doc_id, document in cluster.items():
                # Generate the document URL
                print("Document Type", type(document))
                doc_id = document.obj_id
                print(len(document.embeddings['embedding']))
                print(doc_id)

                # Convert the document to JSON format using the to_dict() method
                json_data = self.to_dict(document)

                # Check embeddings size and truncate if necessary
                
                if isinstance(json_data['fields']['embeddings']['embedding'], list):
                    embeddings = json_data['fields']['embeddings']['embedding']
                    if len(embeddings) > 128:
                        #print("Truncating embeddings to first 128 elements.")
                        json_data['fields']['embeddings']['embedding'] = embeddings[:128]
                

                # Attempt to send the request with retry logic
                for attempt in range(max_retries):
                    try:
                        response = requests.post(url + str(doc_id), headers=headers, json=json_data)
                        
                        # Check response status and print result
                        if response.status_code == 200:
                            print("Document successfully inserted:", response.json())
                            break  # Exit retry loop on success
                        else:
                            print("Failed to insert document.")
                            print("Status code:", response.status_code)
                            print("Response:", response.json())
                            if response.status_code >= 500:
                                print("Server error encountered. Not retrying.")
                                break  # Exit on server error

                    except requests.exceptions.RequestException as e:
                        print(f"Request failed: {e}. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)

     
    
    
    
    
    

# Example usage would go here, initializing YourClass and calling add_memory2 with input data.
                
                
                
    


    

    def get_all_memories(self) -> List[Object]:
        """Retrieve all memories from Vespa AI engine."""
        response = requests.get(f"{self.vespa_url}/docid/{self.ref_id}")
        if response.status_code == 200:
            return [Object(**item) for item in response.json()]
        else:
            print(f"Error retrieving memories: {response.text}")
            return []

    def get_memory(self, query: str) -> Union[Object, None]:
        """Retrieve a specific object by querying its blurb."""
        all_memories = self.get_all_memories()
        for memory in all_memories:
            if query.lower() in memory.blurb.lower():
                return memory
        return None
    
    
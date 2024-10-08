
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

from superpilot.core.store.schema import *

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
file_path='/Users/zestgeek-29/Desktop/Work/superpilot/superpilot/core/memory/reference_object.txt'
def append_to_file(file_path, obj):
    # Open the file in read mode to get existing lines
    with open(file_path, 'r') as file:
        # Read all lines and strip whitespace
        lines = file.readlines()
        
    # Create a set of unique lines
    unique_lines = set(line.strip() for line in lines)

    # Format the new entry
    new_entry = f'{str(obj.source.replace(".pdf", ""))}_{str(obj.obj_id)}'
    
    # Check if the new entry is already in unique lines
    if new_entry not in unique_lines:
        # Open the file in append mode to add the new entry
        with open(file_path, 'a') as file:
            file.write(f'{new_entry}\n')



def read_lines_from_file(file_path):
    # Open the file in read mode
    with open(file_path, 'r') as file:
        # Read all lines and strip any surrounding whitespace/newline characters
        lines = [line.strip() for line in file.readlines()]
    
    # Remove duplicates by converting the list to a set, then back to a list
    unique_lines = list(set(lines))
    
    return unique_lines



def map_response_to_object(response_data: dict) -> Object:
    """Maps JSON response data to an Object instance."""
    
    # Extract fields from response data
    fields = response_data.get('fields', {})
    
    # Extract embeddings separately from fields
    embeddings = fields.get('embeddings', {})
    
    # Process metadata into a dictionary from the 'metadata' field
    metadata_list = fields.get('metadata', [])
    metadata_dict = {item.split(': ')[0]: item.split(': ')[1] for item in metadata_list if ': ' in item}
    
    # Create an instance of Object using the extracted data
    obj_instance = Object(
        blurb=fields.get('blurb', ''),
        content=fields.get('content', ''),  # 'content' is within 'fields'
        source=response_data.get('source', ''),
        type=ObjectType(fields.get('type', 'text')),
        metadata=metadata_dict,
        ref_id=fields.get('ref_id', ''),
        obj_id=fields.get('obj_id', ''),
        privacy=Privacy(fields.get('privacy', 'public')),
        embeddings=embeddings,  # Will include both 'type' and 'values' as-is
        timestamp=datetime.now()  # You can customize this if you have a specific timestamp
    )
    
    return obj_instance

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
            "blurb": str(obj.blurb),
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
                #print("Document Content", document.content)
                doc_id = str(document.source.replace(".pdf", ""))+'_'+str(document.obj_id)
                #print(len(document.embeddings['embedding']))
                print(doc_id)
                append_to_file(file_path,document)
                document.obj_id=doc_id
                

                # Convert the document to JSON format using the to_dict() method
                json_data = self.to_dict(document)
                #print('JSON data',json_data)

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

    def get_memory(self,id:str) -> Object:
        """Retrieve all memories from Vespa AI engine."""
        url=self.store_url + f'{self.schema_name}/{self.schema_name}/docid/{id}'
        '''
        response = requests.get(url)
        if response.status_code == 200:
            print(response.json())
            return(map_response_to_object(response.json()))
        else:
            print(f"Error retrieving memories: {response.text}")
            return None
        '''
        

        try:
            response = requests.get(url)
            response.raise_for_status()
            #print('Respaone.Json:',response.json()) 
            #print() # Raise an error for bad responses
            return (map_response_to_object(response.json()))  # Return the JSON response as a dictionary
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return None

    def get_all_memory(self) ->List[Object]:
        """Retrieve a specific object by querying its blurb."""
        chunks=[]
        lines=read_lines_from_file(file_path)
        for line in lines:
            chunks.append(self.get_memory(line))
        
        return chunks




    def get_all_doc_ids(self):
        """
        Retrieves a list of all document IDs from the Vespa.ai endpoint.

        Returns:
            list: A list of all document IDs.
        """
        url =self.store_url + f'{self.schema_name}/{self.schema_name}/docid/'
        print('Url',url)
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Log the raw response to understand its structure
            print("Raw response:", response.text)
            
            # Check if the response is a JSON object
            documents = response.json()
            
            # Ensure that we are dealing with a list or dict
            doc_ids = []
            if isinstance(documents, dict):
                if 'documents' in documents:
                    # Extract IDs from the documents list
                    doc_ids = [doc['id'].split('::')[1] for doc in documents['documents']]
                else:
                    print("No 'documents' key found in the response.")
            elif isinstance(documents, list):
                # If it's a list, process each item
                doc_ids = [doc['id'].split('::')[1] for doc in documents]
            
            return doc_ids
            
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return []
        

    
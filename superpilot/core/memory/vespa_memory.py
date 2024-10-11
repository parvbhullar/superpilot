
from superpilot.core.store.schema import Object

import requests
from datetime import datetime
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
from superpilot.core.store.search.retrieval.query_escalator import generate_keywords_and_sentences
from superpilot.core.memory.documentation import _process_file
#vespa_url="http://localhost:8080/document/v1/<namespace>/<document-type>/"


import numpy as np

import os
#import datetime
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
import PyPDF2

# Load a pre-trained sentence transformer model for embedding generation
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings(text):
    """
    Generate a 128-dimensional embedding for the given text using a pre-trained model.
    """
    embedding = model.encode(text)
    # Trim or pad the embedding to be exactly 128 dimensions (if necessary)
    if len(embedding) > 128:
        embedding = embedding[:128]
    elif len(embedding) < 128:
        embedding = list(embedding) + [0.0] * (128 - len(embedding))
    
    return embedding.tolist()
    

    
    # Generate the initial embedding
    
    

def extract_metadata(file_path):
    """
    Extract metadata from the file such as file size, creation date, last modified date,
    and, for PDFs, the number of pages.
    """
    metadata = {
        "file_name": os.path.basename(file_path),
        "file_size": str(os.path.getsize(file_path)),  # Convert file size to string
        "file_path": file_path,
        "creation_date": datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
        "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # If the file is a PDF, we can also extract the number of pages
    if file_path.lower().endswith('.pdf'):
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadata["num_pages"] = str(len(reader.pages))  # Convert number of pages to string
        except Exception as e:
            metadata["num_pages"] = "Error reading PDF: " + str(e)
    
    return metadata


def first_sentence(text):
    """
    Extract the first sentence from the text.
    """
    sentences = text.split('.')
    return sentences[0].strip() + '.' if sentences else text

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


import requests
#from superpilot.core.memory.vespa_memory import map_response_to_object

def convert_response_to_objects(response: List[Dict[str, Any]]) -> List[Object]:
    """Converts a JSON response into a list of Object instances."""
    objects_list = []
    
    for item in response:
        obj_instance = map_response_to_object(item)
        objects_list.append(obj_instance)
    
    return objects_list



from unstructured.partition.auto import partition

import time
class MemoryManager:
    def __init__(self, store_url: str, ref_id: str, schema_name: str=None):
        self.store_url = store_url
        self.ref_id = ref_id
        self.schema_name =  schema_name or "object_schema"

    
    def convert_to_objects(self,input_data: Union[str, dict]):
        results=asyncio.run(call_main_function(input_data))
        return(results)
    
    def process_document(self,document):
        elements = document.elements
        print("Elements Created")  # Partition the file into elements
        ref_id = document.id # Use the file base name as ref_id
        objects = []  # List to store generated objects
        
        for i, element in enumerate(elements, start=1):
            obj = Object(
                blurb=first_sentence(element.text),
                ref_id=ref_id,
                obj_id=f"{ref_id}_{i}",
                content=str(element.text),
                source=str(document.source),
                privacy='public',
                embeddings={"embedding": generate_embeddings(element.text)},
                metadata=document.metadata,
                type='text'
            )
            objects.append(obj)
        print('Objects Created')
        return objects
    
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
                f"file_name: {obj.metadata['file_name']}",
                f"file_size: {obj.metadata['file_size']}",
                f"file_path: {obj.metadata['file_path']}",
                f"creation_date: {obj.metadata['creation_date']}",
                f"last_modified: {obj.metadata['last_modified']}",
                
            ],
            "type": obj.type
            }
        }
    
    
    

    
        

    def add_memory(self, input_data):
        """Add memory to Vespa AI engine."""
        results = self.process_document(input_data)
        print('Result Type', type(results))
        
        max_retries = 5
        retry_delay = 2
        namespace = "testing"
        document_type = "unpod_chunk"
        
        url = self.store_url + f'document/v1/{self.schema_name}/{self.schema_name}/docid/'
        print('Url', url)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer YOUR_ACCESS_TOKEN'  # Replace with your actual access token if required
        }       

        # Retry logic for sending POST requests to Vespa
        
        for document in results:
            
                
            # Generate the document URL
            #print("Document Content", document.content)
            doc_id = str(document.obj_id)
            print('Emeddings Length',len(document.embeddings['embedding']))
            print(doc_id)
            append_to_file(file_path,document)
            #document.obj_id=doc_id
            
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

                  
    

    def execute_query(self, query: str, embedding: Optional[List[float]] = None) -> List[Object]:
        """Executes a search query against the Vespa endpoint and returns a list of Object instances."""
        try:
            params = {'yql': query}
            if embedding is not None:
                params['embedding'] = embedding  # Pass the embedding if provided
            
            response = requests.get(self.store_url + 'search/', params=params, timeout=20)  # Set a timeout
            response.raise_for_status()  # Raise an error for bad responses
            
            results = response.json().get('root', {}).get('children', [])
            objects = convert_response_to_objects(results)

            return objects
        
        except requests.exceptions.Timeout:
            print("The request timed out.")
            return []
        
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return []

    def search(self, query: str, filters: Optional[Dict[str, Union[str, List[str]]]] = None) -> List[Object]:
        """Searches for objects in Vespa based on a query string and optional filters."""
        
        # Generate embeddings for the query
        embedding = generate_embeddings(query)

        # Base query construction
        base_query = f"SELECT * FROM object_schema WHERE content MATCHES '{query}'"
        
        # Adding filters if available
        if filters:
            filter_conditions = []
            
            if 'type' in filters:
                filter_conditions.append(f"type == '{filters['type']}'")
            
            if 'metadata' in filters:
                metadata_conditions = [f"metadata CONTAINS '{meta}'" for meta in filters['metadata']]
                filter_conditions.append(' OR '.join(metadata_conditions))
            
            if 'blurb' in filters:
                filter_conditions.append(f"blurb MATCHES '{filters['blurb']}'")
            
            if 'source' in filters:
                filter_conditions.append(f"source == '{filters['source']}'")
            
            if filter_conditions:
                base_query += " AND " + " AND ".join(filter_conditions)
        
        # Execute the constructed query with optional embedding
        return self.execute_query(base_query, embedding)



    
    def search_objects(self,query: str, filters: Optional[Dict[str, Union[str, List[str]]]] = None,iterations:int = 1) -> List[Object]:
        """Searches for objects in Vespa based on a query string and optional filters."""
        
        # Generate keywords from the main query
        print('In Search Objects')
        keywords_and_sentences = generate_keywords_and_sentences(query)
        #print("Keywords:",keywords_and_sentences)
        # Extract only the keywords from the response
        keywords = list(set(keywords_and_sentences))  # Adjust if needed
        #print("Keywords:",keywords)
        # Iteratively generate additional keywords
        for _ in range(iterations):
            new_keywords = []
            for keyword in keywords:
                generated_keywords = generate_keywords_and_sentences(keyword)  # Generate keywords from existing keywords
                new_keywords.extend(list(set(generated_keywords)))  # Avoid duplicates
            keywords.extend(new_keywords)
            #print("Keywords:",keywords)
            print()
            print()

        print("Keywords Generation Complete")

        
        #return keywords
        print('Keywords',keywords)
        
        all_results = []

        # Iterate over each keyword and perform a search
        for keyword in keywords:
            #print(f"Searching for keyword: {keyword}")
            
            # Base query construction
            base_query = f"SELECT * FROM object_schema WHERE content MATCHES '{keyword}'"
            
            # Adding filters if available
            if filters:
                filter_conditions = []
                
                if 'type' in filters:
                    filter_conditions.append(f"type == '{filters['type']}'")
                
                if 'metadata' in filters:
                    metadata_conditions = [f"metadata CONTAINS '{meta}'" for meta in filters['metadata']]
                    filter_conditions.append(' OR '.join(metadata_conditions))
                
                if 'blurb' in filters:
                    filter_conditions.append(f"blurb MATCHES '{filters['blurb']}'")
                
                if 'source' in filters:
                    filter_conditions.append(f"source == '{filters['source']}'")
                
                if filter_conditions:
                    base_query += " AND " + " AND ".join(filter_conditions)

            # Execute the constructed query
            results = self.execute_query(base_query)
            all_results.extend(results)  # Combine results from each keyword
        
        return all_results
    




    def ingest(self,source:str,ingest_type:str,ingest_config:dict,save:bool):
        
        file_name=os.path.basename(source)
        document=_process_file(file_name=file_name,file=source,pdf_pass=None)
        print('Document Created')
        

        return document

    
        



        




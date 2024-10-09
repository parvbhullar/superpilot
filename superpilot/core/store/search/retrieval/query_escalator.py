import transformers

from transformers import pipeline

# Load a pretrained language model

#generator = pipeline("text-generation", model="gpt-3.5-turbo")

import openai
import os
import re

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_keywords_and_sentences(prompt, model="gpt-3.5-turbo", max_tokens=150, temperature=0.7):
    # Create a prompt to generate keywords and one-line sentences
    print('In Generate Keywords')
    
    formatted_prompt = f"Generate a list of 1-4 word keywords and one-line sentences related to: {prompt}. Provide the result as a list."

    # Call the OpenAI API
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an assistant that generates keywords and sentences."},
            {"role": "user", "content": formatted_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        n=1
    )
    response_text = response['choices'][0]['message']['content']
    # Extracting the text response from the model
    lines = response_text.splitlines()
    clean_list = []

    for line in lines:
        # Ignore empty lines and labels like 'Keywords:' or 'Sentences:'
        if line.strip() and not line.startswith('Keywords') and not line.startswith('Sentences'):
            # Remove leading hyphens and whitespace
            cleaned_line = re.sub(r'^\d+\.\s*', '', line)  # Remove leading numbers (1. , 2. , etc.)
            cleaned_line = cleaned_line.lstrip('-').strip()  # Remove leading hyphens and trim whitespace
            if cleaned_line:  # Check if the line is not empty after cleaning
                clean_list.append(cleaned_line)
    
    return clean_list
    
    
    
    # Return the result as a list of strings
    #return keywords_and_sentences.splitlines()








# Input string


import numpy as np
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from superpilot.core.store.base import Object

# Initialize a model for creating embeddings (Sentence-BERT or similar)
  # Example, you can use others like 'paraphrase-MiniLM-L6-v2'




def retrieve_related_objects(objects: List[Object], query: str, top_n: int = 5) -> List[Object]:
    """
    Retrieves the top N objects related to the query based on content similarity.

    Args:
        objects (List[Object]): List of Object instances to search through.
        query (str): The query string to search for relevant content.
        top_n (int): Number of top relevant objects to return.

    Returns:
        List[Object]: The most relevant objects related to the query.
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # Step 1: Embed the query using the NLP model
    query_embedding = model.encode(query)

    # Step 2: Embed all objects' content using the same model
    object_embeddings = [model.encode(obj.content) for obj in objects]

    # Step 3: Compute cosine similarities between the query and each object's content
    similarities = cosine_similarity([query_embedding], object_embeddings)[0]

    # Step 4: Get indices of the top N most similar objects
    top_indices = np.argsort(similarities)[-top_n:][::-1]

    # Step 5: Retrieve the top N most similar objects based on the computed similarities
    top_objects = [objects[i] for i in top_indices]

    return top_objects


def retrieve_objects(objects: List[Object], query: str, top_n: int = 5,similarity_threshold: float = 0.5,iterations:int = 1) -> List[Object]:
    """
    Retrieves the top N objects related to the query based on content similarity and keyword matching.

    Args:
        objects (List[Object]): List of Object instances to search through.
        query (str): The query string to search for relevant content.
        top_n (int): Number of top relevant objects to return.

    Returns:
        List[Object]: The most relevant objects related to the query.
    """
    print('In Retrieve_Objects')
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Step 1: Generate keywords and sentences related to the query
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

    '''
    matched_objects = []  # Use a set to avoid duplicates
    print("Running Query")
    # Step 2: Check semantic similarity of each object with each keyword
    for obj in objects:
        obj_embedding = model.encode(obj.content)  # Embed object content

        for keyword in keywords:
            keyword_embedding = model.encode(keyword)  # Embed the keyword

            if keyword in obj.content:
                matched_objects.append(obj)
            # Compute similarity
            similarity_score = cosine_similarity([obj_embedding], [keyword_embedding])[0][0]
            #similarity_score = cosine_similarity([keyword_embedding], obj_embedding)[0]
            # Check if the similarity score exceeds the threshold
            if similarity_score >= similarity_threshold:
                matched_objects.append(obj)  # Add to the set of matched objects
                break  # Break the loop to avoid adding the same object multiple times
    '''


    print("Query Starting")
    keyword_embeddings = {keyword: model.encode(keyword) for keyword in keywords}

# Create a set of keywords for O(1) membership testing
    keyword_set = set(keywords)

    # Initialize list to store matched objects
    matched_objects = []

    for obj in objects:
        obj_embedding = model.encode(obj.content)  # Embed object content
        
        # Check if any keyword is in obj.content using set for O(1) complexity
        if any(keyword in obj.content for keyword in keyword_set):
            matched_objects.append(obj)
            continue  # Skip similarity check if we already matched

        # Compute all similarities at once using NumPy
        similarities = cosine_similarity([obj_embedding], list(keyword_embeddings.values()))[0]

        # Check if any similarity score exceeds the threshold
        if np.any(similarities >= similarity_threshold):
            matched_objects.append(obj)
    # Convert matched_objects set back to list
    matched_objects = list(matched_objects)
    print(len(matched_objects))
    # Step 3: If there are no matches, return the top N based on content similarity
    if not matched_objects:
        # Embed the query using the NLP model
        query_embedding = model.encode(query)

        # Embed all objects' content using the same model
        object_embeddings = [model.encode(obj.content) for obj in objects]

        # Compute cosine similarities between the query and each object's content
        similarities = cosine_similarity([query_embedding], object_embeddings)[0]

        # Get indices of the top N most similar objects
        top_indices = np.argsort(similarities)[-top_n:][::-1]

        # Retrieve the top N most similar objects based on the computed similarities
        top_objects = [objects[i] for i in top_indices]
        
        return top_objects

    # Step 4: Return the matched objects
    return matched_objects

def remove_duplicate_objects(objects: List[Object]) -> List[Object]:
    """
    Removes duplicate objects from the list based on the obj_id attribute.

    Args:
        objects (List[Object]): List of Object instances from which duplicates will be removed.

    Returns:
        List[Object]: List of unique Object instances based on obj_id.
    """
    print('In Remove Duplicates Objects')
    seen_ids = set()
    unique_objects = []

    for obj in objects:
        if obj.obj_id not in seen_ids:
            unique_objects.append(obj)
            seen_ids.add(obj.obj_id)

    return unique_objects



from typing import Any,Optional,Dict,Union
from superpilot.core.memory.vespa_memory import MemoryManager
def search_objects_chunks(objects: List[Object],query: str, filter_dict: Dict[str, Any]) -> List[Object]:
    """
    Searches for objects related to the query while applying the provided filters.

    Args:
        objects (List[Object]): List of Object instances to search through.
        query (str): The query string to search for relevant content.
        filter (Dict[str, Union[str, Dict]]): A dictionary of filters to apply to the results.
        top_n (int): Number of top relevant objects to return.

    Returns:
        List[Object]: The filtered and most relevant objects related to the query.
    """
    print('In Search Function')
    
    chunks=objects
    

    if len(chunks)>0:
        print('Chunks loaded')
    # Step 1: Use the existing retrieve_related_objects function to get top objects
        objects = remove_duplicate_objects(retrieve_objects(chunks, query))
        print('Number of Objects after Retrieve',len(objects))
        print('Blurb Example',objects[12].blurb)
        


        if not filter_dict:
            return objects

        # Step 2: Filter top_objects based on the provided filter
        matching_objects = []

        for obj in objects:
            # Check if the object matches the filter criteria
            matches_all = True  # Start assuming it matches all

            for key, value in filter_dict.items():
                if hasattr(obj, key):
                    obj_value = getattr(obj, key)

                    # Handle metadata filtering
                    if key == "metadata":
                        if not any(item in obj_value.items() for item in value.items()):
                            matches_all = False
                            break
                    elif obj_value != value:
                        matches_all = False
                        break

            if matches_all:
                matching_objects.append(obj)

        return matching_objects
    
    else:
        print('No Chunks Found')
        return []


#-----------------------------------------------------------------#
# Vespa Query Operations 

import requests
from superpilot.core.memory.vespa_memory import map_response_to_object

def convert_response_to_objects(response: List[Dict[str, Any]]) -> List[Object]:
    """Converts a JSON response into a list of Object instances."""
    objects_list = []
    
    for item in response:
        obj_instance = map_response_to_object(item)
        objects_list.append(obj_instance)
    
    return objects_list



def execute_query(query: str) -> List[Object]:
    """Executes a search query against the Vespa endpoint and returns a list of Object instances."""
    try:
        response = requests.get("http://localhost:8081/search/", params={'yql': query}, timeout=20)  # Set a timeout
        response.raise_for_status()  # Raise an error for bad responses
        
        results = response.json().get('root', {}).get('children', [])
        #print("Response")
        #print(results)
        objects=convert_response_to_objects(results)

        
        
        # Map results back to Object instances
        return objects
    
    except requests.exceptions.Timeout:
        print("The request timed out.")
        return []
    
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return []

def search(query: str, filters: Optional[Dict[str, Union[str, List[str]]]] = None) -> List[Object]:
    """Searches for objects in Vespa based on a query string and optional filters."""
    
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
    
    # Execute the constructed query
    return execute_query(base_query)



def search_objects(query: str, filters: Optional[Dict[str, Union[str, List[str]]]] = None,iterations:int = 1) -> List[Object]:
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
        results = execute_query(base_query)
        all_results.extend(results)  # Combine results from each keyword
    
    return all_results
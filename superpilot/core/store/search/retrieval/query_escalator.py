import spacy
import numpy as np
import faiss  # Ensure to install faiss-cpu or faiss-gpu based on your system
from typing import List
from transformers import AutoModel, AutoTokenizer
from superpilot.core.store.base import Object

# Load a spaCy model for keyword extraction
nlp = spacy.load("en_core_web_sm")

# Load a good and open-source LLM model from Hugging Face
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")



def extract_keywords_and_sentences(query: str) -> List[str]:
    """
    Extracts all possible keywords and relevant sentences from the query string.

    Args:
        query (str): The query string.

    Returns:
        List[str]: A list of keywords and sentences generated from the query.
    """
    doc = nlp(query)
    
    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN", "VERB", "ADJ"]]
    sentences = [sent.text for sent in doc.sents]
    
    return list(set(keywords + sentences))


def retrieve_related_objects(objects: List[Object], query: str, top_n: int = 5) -> List[Object]:
    """
    Retrieves all objects related to the query based on keyword and content similarity.

    Args:
        objects (List[Object]): List of Object instances to search through.
        query (str): The query string to search for relevant content.
        top_n (int): Number of top relevant objects to return.

    Returns:
        List[Object]: The most relevant objects related to the query.
    """
    # Step 1: Extract keywords and sentences from the query
    keywords_and_sentences = extract_keywords_and_sentences(query)

    # Step 2: Embed all extracted keywords/sentences
    query_embeddings = model(**tokenizer(keywords_and_sentences, return_tensors="pt", padding=True, truncation=True))
    
    # Step 3: Embed all object content
    object_contents = [obj.content for obj in objects]
    object_embeddings = model(**tokenizer(object_contents, return_tensors="pt", padding=True, truncation=True))

    # Convert embeddings to numpy array
    query_embedding_np = query_embeddings['last_hidden_state'].mean(dim=1).detach().numpy().astype('float32')
    object_embedding_np = object_embeddings['last_hidden_state'].mean(dim=1).detach().numpy().astype('float32')

    # Step 4: Create a FAISS index for the object embeddings
    index = faiss.IndexFlatL2(object_embedding_np.shape[1])  # Using L2 distance
    index.add(object_embedding_np)  # Add object embeddings to the index

    # Step 5: Perform a search in the index for the nearest neighbors of the query
    distances, indices = index.search(query_embedding_np, top_n)

    # Step 6: Retrieve the top N most similar objects based on the indices returned
    top_objects = [objects[i] for i in indices[0]]

    return top_objects


def search(objects: List[Object], query: str, filter: Optional[Dict[str, Union[str, Dict]]] = None, top_n: int = 5) -> List[Object]:
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
    
    # Step 1: Use the existing retrieve_related_objects function to get top objects
    top_objects = retrieve_related_objects(objects, query, top_n)

    # Step 2: Filter top_objects based on the provided filter
    if filter:
        filtered_objects = []
        
        for obj in top_objects:
            match = True
            
            for key, value in filter.items():
                if value is not None:
                    if key == 'metadata':
                        # Check if metadata matches any of the filters
                        if not any(k in obj.metadata and obj.metadata[k] == v for k, v in value.items()):
                            match = False
                    elif getattr(obj, key) != value:
                        match = False
            
            if match:
                filtered_objects.append(obj)

        return filtered_objects
    
    return top_objects
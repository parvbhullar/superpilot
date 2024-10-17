import sys
import os
import asyncio

# Add the parent directory to the system path for imports
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.memory.vespa_memory import MemoryManager

from datasets import Dataset 
from ragas.metrics import answer_relevancy,faithfulness, answer_correctness
from ragas import evaluate
import pandas as pd
#Doc api evaluation


# Add the parent directory to the system path for imports
#openai_api_key=os.getenv('OPENAI_API_KEY')

import requests
import time


def get_response(query):
    
    # Define the URL and the payload
    url = "http://qa-search-service.co/api/v1/search/query/docs/?page=1&page_size=1"
    payload = {
        "query": query,
        "kn_token": []
    }

    # Measure the time taken for the request
    start_time = time.time()
    response = requests.post(url, json=payload,timeout=5)
    end_time = time.time()

    # Calculate the response time
    response_time = end_time - start_time

    # Print the response status code, time taken, and the response data
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Time: {response_time:.4f} seconds")
    result=response.json()
    main_content=str(result["data"][0]["content"])

    #print (main_content)
    print()
    return main_content,response_time


def doc_eval_value(question:str,ground_truth:str):
    answer,times=get_response(question)

    data_samples={
                'question':[question],
                'answer':[answer],
                'ground_truth':[ground_truth],
            }
    
    dataset = Dataset.from_dict(data_samples)
    score = evaluate(dataset,metrics=[answer_correctness])
    sc=score.to_pandas()

    eval_value=sc['answer_correctness']

    return eval_value   


def get_eval(question: list, ground_truth: list, answer: list):
    # Optimized evaluation: vectorized/batched processing
    data_samples = {
        'question': question,
        'answer': answer,
        'ground_truth': ground_truth,
    }

    dataset = Dataset.from_dict(data_samples)
    
    # Assuming 'evaluate' and 'answer_correctness' are already optimized or a fast metric is used
    score = evaluate(dataset, metrics=[answer_correctness])
    sc = score.to_pandas()
    
    eval_value = sc['answer_correctness']

    return eval_value
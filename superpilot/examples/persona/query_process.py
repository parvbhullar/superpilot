import asyncio
import os
import sys
import argparse
import json
from typing import Any
import time
import requests
from datasets import Dataset 
from ragas.metrics import answer_relevancy,faithfulness, answer_correctness
from ragas import evaluate
import pandas as pd

from superpilot.examples.evals.doc_eval import get_eval
from superpilot.examples.persona.schema import Message, User, Role, Context
from superpilot.examples.persona.handler import PersonaHandler
from superpilot.examples.persona.citation_processing import get_citation
from superpilot.examples.persona.followup_gen import FollowUpGenExecutor
async def get_agent_response(query):
    
    # Define the URL and the payload
    url = "http://qa-search-service.co/api/v1/search/query/agents/?page=1&page_size=1"
    payload = {
        "query": query,
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
    agent_json=result["data"][0]["metadata"]
    return agent_json




def get_docs(query, ground_truth):
    citations = {}
    citation_num = {}
    eval_docs = []
    url = "http://qa-search-service.co/api/v1/search/query/docs/"
    payload = {
        "query": query,
        "kn_token": []
    }

    # Measure the time taken for the request
    start_time = time.time()

    # Send the request with a timeout and handle exceptions
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()  # Ensure an error is raised for unsuccessful status codes
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return [], {}, {}

    end_time = time.time()
    response_time = end_time - start_time

    # Print the response status code and time taken
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Time: {response_time:.4f} seconds")
    
    result = response.json()
    print('Response Length', len(result["data"]))

    # Extract documents with content length > 250 words
    answers = [str(doc["content"]) for doc in result["data"] if len(str(doc["content"]).split()) > 250]
    
    # If no valid documents, return early
    if not answers:
        return [], {}, {}

    n = len(answers)
    print("Length of contents", n)

    # Prepare inputs for evaluation in a batch
    question = [query] * n
    ground_truths = [ground_truth] * n
    
    # Batch evaluation (optimizing this part by using get_eval in parallel)
    score = get_eval(question=question, ground_truth=ground_truths, answer=answers)
    print("Score List", score)
    
    # Filter documents based on score > 0.20 and collect citations
    for idx, (doc, score_value) in enumerate(zip(result["data"], score), start=1):
        if score_value > 0.20:
            eval_docs.append(doc)
            citations[str(idx)] = len(str(doc["content"]))  # Assuming 'content' size as a reference
            citation_num[str(idx)] = doc["document_id"]  # Use document_id for reference

    print("Len of Eval Docs:", len(eval_docs))
    
    return (eval_docs)


def add_citations(response, docs):
    citations = {}
    citation_num = {}
    citation_index = 1
    for i, doc in enumerate(docs):
        doc_content = doc["content"]
        doc_id = doc["document_id"]
        
        # Find if doc_content appears in response text
        if doc_content in response:
            # Count the length of characters used
            content_length = len(doc_content)
            
            # Add citation number in response text
            citation_placeholder = f"{citation_index}"
            response = response.replace(doc_content, doc_content + citation_placeholder)
            
            # Update the citations and citation_num dictionaries
            citations[str(citation_index)] = content_length
            citation_num[str(citation_index)] = doc_id
            
            # Increment citation index for next document
            citation_index += 1
            
    return response, citations, citation_num




async def query_process_agent(query:str,ground_truth):
    
    
    
    agent= {
                "persona_name": "HeritageReviver",
                "tags": [
                    "preservation architecture",
                    "adaptive reuse",
                    "historic buildings",
                    "community development",
                    "Midwestern towns"
                ],
                "handle": "heritage-reviver",
                "about": "An expert in preservation architecture focusing on revitalizing historic commercial buildings in Midwestern communities, ensuring the balance between historical integrity and modern utility.",
                "persona": "HeritageReviver is dedicated to the adaptive reuse of historic commercial buildings, emphasizing the importance of preserving the architectural heritage of Midwestern towns. By revitalizing Main Street USA, HeritageReviver explores how these efforts positively affect community identity and economic development. With a focus on sustainability and resilience, this persona highlights how careful preservation can foster a sense of place while addressing contemporary needs. Through thoughtful integration of old structures into modern uses, HeritageReviver aims to inspire communities to cherish their history while embracing future growth.",
                "knowledge_bases": [
                    "Preservation Architecture Resources",
                    "Midwestern Heritage Studies",
                    "Community Development Initiatives"
                ]
            }
    try:

        data= get_docs(query, ground_truth)
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return None
    
    block_json={
        'content':query,
        'data':data
    }
    agent["data"]=data
    agent["query"]=query
    

    #msg=Message.from_block(block_json)
    
    message = Message.create(message=query)
    message=message.from_block(block_json)
    print("Message")
    #print(message)
    print("Message Complete")
    

    #citations=get_citation(data)

    print("Agent")
    #print(agent)
    print()
    try:
        agent = agent.get("metadata", agent)
        if not agent.get("persona", None):
            print(f"Error finding agent {agent}.")
            return None
        
        #print("Persona",agent)
        print()

        pilot = PersonaHandler.from_json(agent)
        pilot._agent_data={"data":data}

        response = await pilot.execute(message, Context.factory("Session1"),None)
        #print(response)
        msg = Message.from_model_response(response, message.session_id,
                                          User.add_user(pilot.name(), Role.ASSISTANT, data=pilot.dump()))
        print('Msg Generated')
        #print(msg)

        new_msg,citations,citation_num=add_citations(str(msg.message),data)
        #citations=get_citation(docs=data,msg=str(msg.message))

        followup=FollowUpGenExecutor()
        followup_response=await followup.execute(query=query,response=str(msg.message))

        print('Followup Generated')
        #print(followup_response)
        
        docs = [
            {k: v for k, v in doc.items() if k != "content" and k != "metadata"}
            for doc in data
                    ]
        for doc in docs:
            if "metadata" in doc and "main_content" in doc["metadata"]:
                del doc["metadata"]["main_content"]
        
        response={
            'message':new_msg,
            'ref_docs':docs,
            'citations':citations,
            "citation_num":citation_num,
            'followup_questions':followup_response['followup_questions']
            
        }
        return response
        
    except Exception as e:
        print(f"Error calling agent :{str(e)}")
        return None







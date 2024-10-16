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

from superpilot.examples.persona.schema import Message, User, Role, Context
from superpilot.examples.persona.handler import PersonaHandler
from superpilot.core.evals.doc_eval import get_eval
from superpilot.examples.persona.citation_processing import get_citation
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




async def get_docs(query,ground_truth):
    eval_docs=[]
    url = "http://qa-search-service.co/api/v1/search/query/docs/"
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
    answers=[]
    print('Response Length',len(result["data"]))
    # for doc in result["data"]:
    #     main_content=str(doc["content"])
    #     if len(main_content.split())>300:
    #         score=get_eval(question=main_content,ground_truth=ground_truth,answer=main_content)
    #         if (score.iloc[0])>0.7:
    #             eval_docs.append(doc)

    for doc in result["data"]:
        main_content=str(doc["content"])
        if len(main_content.split())>250:
            answers.append(main_content)
    
    n=len(answers)
    print("Length of contents",n)
    question=[query]*n
    ground_truths=[ground_truth]*n
    score=get_eval(question=question,ground_truth=ground_truths,answer=answers)
    print("Score List",score)
    
    for doc, score_value in zip(result["data"], score):
        if score_value > 0.20:
            eval_docs.append(doc)

    #print (main_content)
    print("Len of Eval Docs")
    print(len(eval_docs))
    #print(eval_docs[0])
    return eval_docs





async def query_process_agent(query:str,ground_truth):
    agent, data = await asyncio.gather(
        get_agent_response(query),
        get_docs(query, ground_truth)
    )
    message = Message.create(message=query,data=data)

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
        response = await pilot.execute(message, Context.factory("Session1"), None)
        print(response)
        msg = Message.from_model_response(response, message.session_id,
                                          User.add_user(pilot.name(), Role.ASSISTANT, data=pilot.dump()))
        print('Msg Generated')


        citations=get_citation(docs=data,msg=str(msg.message))


        

        response={
            'message':msg.message,
            'citations':citations
        }
        return response
        
    except Exception as e:
        print(f"Error calling agent {agent}: {str(e)}")
        return None







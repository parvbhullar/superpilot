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




async def get_docs(query,ground_truth):
    citations={}
    citation_num={}
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
    
    for idx, (doc, score_value) in enumerate(zip(result["data"], score), start=1):
        if score_value > 0.20:
            eval_docs.append(doc)
            citations[str(idx)] = len(str(doc["content"]))  # Assuming 'id' is a unique identifier in doc
            citation_num[str(idx)] = doc["document_id"]  # Create a citation reference


    #print (main_content)
    print("Len of Eval Docs")
    print(len(eval_docs))
    #print(eval_docs[0])
    return eval_docs,citations,citation_num





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

    data,citations,citation_num = await get_docs(query, ground_truth)
    
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
        #print(response)
        msg = Message.from_model_response(response, message.session_id,
                                          User.add_user(pilot.name(), Role.ASSISTANT, data=pilot.dump()))
        print('Msg Generated')


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
            'message':msg.message,
            'ref_docs':docs,
            'citations':citations,
            "citation_num":citation_num,
            'followup_questions':followup_response['followup_questions']
            
        }
        return response
        
    except Exception as e:
        print(f"Error calling agent :{str(e)}")
        return None







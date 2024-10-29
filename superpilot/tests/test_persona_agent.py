import sys
import os
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from typing import Dict

from superpilot.examples.persona.schema import Message, User, Role, Context
# from superpilot.core.planning import LanguageModelClassification, LanguageModelResponse, PromptStrategy
from superpilot.core.store.chat.chat_models import LlmDoc
from superpilot.core.store.vectorstore.vespa.configs.constants import DocumentSource
from superpilot.examples.persona.answering.simple_answer import SimpleAnswer
from superpilot.examples.persona.answering.agent import PersonaAgent
query='Most important Historical Event of 21st Century'
persona={
                "persona_name": "IT Policy Creator",
                "tags": [
                    "Policy Creator",
                    "It Policies",
                    "Security Policies"
                ],
                "handle": "it-policy-creator",
                "about": "I help you to create IT policies for the businesses i.e. Information Security policy, Device Security Policy and many more.",
                "persona": "You are an experienced IT policy specialist specialising in creating comprehensive and tailored IT policies for businesses. I need your help to develop several IT policies for my organization, including but not limited to:\n\nInformation Security Policy\nDevice Security Policy\nData Protection Policy\nNetwork Security Policy\nAcceptable Use Policy\nRequirements:\n\nCustomization: The policies should be tailored to a small/medium/large business.\n\nStructure: Each policy should include the following sections:\n\nPurpose\nScope\nPolicy Statement\nRoles and Responsibilities\nProcedures\nCompliance and Enforcement\nReview and Maintenance\nContent Guidelines:\n\nCompliance: Ensure policies align with relevant laws and regulations such as GDPR, HIPAA, or other industry-specific standards.\nClarity: Use clear and concise language that is easily understandable by all employees.\nComprehensiveness: Cover key areas such as data protection, access controls, incident response, employee training, and acceptable use of company resources.\nPracticality: Provide actionable procedures and guidelines that can be realistically implemented within the organization.\nAdditional Information:\n\nHighlight any industry best practices that should be incorporated.\nConsider any potential risks specific to the industry or company size.\nEmphasize the importance of employee adherence and outline consequences for non-compliance.\nObjective:\n\nDeliver a set of well-structured, comprehensive IT policies that will enhance our organization's security posture and ensure compliance with all relevant regulations.",
                "knowledge_bases": [
                    "KPVTVCGZ61XUD37VRZGEUBZG",
                    "PZ0ATSKMK9J3ST3ZVELRKCP9"
                ]
            }

import time
import requests
def get_response(query):
    
    
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
    return(result["data"])


def to_LlmDoc():
    
    
    try:
        data=get_response(query)
        print('Response Length', len(data))
        llm_docs=[]
        for d in data:
            llm_doc = LlmDoc(
                document_id=d["document_id"],
                content=d["content"],
                blurb=d["blurb"],
                semantic_identifier=d["semantic_identifier"],
                source_type=DocumentSource(d["source_type"]),
                metadata=d["metadata"],
                updated_at=None,
                link=d.get("link"),
                source_links=d.get("source_links")
            )
            llm_docs.append(llm_doc)
        return(llm_docs)

    except Exception as e:
        print(f"Error processing data: {e}")
        return []

        

    


# 


async def generate_simple_answer(query: str, persona: Dict[str, str]):
    try:
        data = to_LlmDoc()  # Assuming this function is defined elsewhere and returns a list of documents.
        answer_generator = SimpleAnswer(question=query, docs=data, persona=persona)
        
        print("Simple Answer Response:")
        c=1
        async for response in answer_generator.llm_answer:
            print(c,":",response)
            print()
            c+=1
    except Exception as e:
        print(f"Error generating response: {e}")
        print('No Data Found')


async def persona_agent():
    data = to_LlmDoc()
    message=Message.create(message=query,data=data)
    pilot = PersonaAgent.from_json(persona)
        # pilot = DSPyHandler.from_json(agent)
    response = await pilot.execute(message, Context.factory("Session1"), None)
    print("Response from persona agent")
    print(response)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_simple_answer(query=query, persona=persona))
    #loop.run_until_complete(persona_agent())
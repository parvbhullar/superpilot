import sys
import os
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


#from superpilot.examples.persona.answering.agent import PersonaAgent
# from superpilot.examples.persona.schema import Message, User, Role, Context
# from superpilot.core.planning import LanguageModelClassification, LanguageModelResponse, PromptStrategy
from superpilot.core.store.chat.chat_models import LlmDoc
from superpilot.core.store.vectorstore.vespa.configs.constants import DocumentSource
from superpilot.examples.persona.answering.simple_answer import SimpleAnswer
query='Most important Historical Event of 21st Century'
persona={
                "persona_name": "Multi-AI",
                "tags": [
                    "Prompt Engineering"
                ],
                "handle": "multi-ai",
                "about": "Multi-AI Based Response",
                "persona": "You are MultiAIGPT, An advanced AI system designed to handle multiple tasks simultaneously, providing efficient and accurate responses based on the user's input.",
                "knowledge_bases": [],
                "query":query
            }

from openai import OpenAI
def openai_response():
    
    client = OpenAI()

    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"{query}"}
    ]
    )
    print("Resposne")
    print(completion.choices[0].message)








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

        

    


# async def generate_response():
#     # Generate a response based on the provided input
#     # Example: fetch data from an API based on the input, apply necessary transformations, and return the response
    
#     try:
#         data=get_response(query)
#         docs={
#             "data":data
#         }
#         message=Message.create(message=query,data=data)
#         #message.data=data
#         persona_agent=PersonaAgent.from_json(json_data=persona)
#         persona_agent._agent_data=persona
#         response= await persona_agent.execute(message,Context.factory("Session1"))
#         # answer=SimpleAnswer(question=query,docs=data,persona=persona,llm=persona_agent._providers[LanguageModelClassification.SMART_MODEL])
#         # print(answer.llm_answer())
#         print(response)
#     except Exception as e:
#         print(f"Error generating response: {e}")
#         print('No Data Found')


async def generate_simple_answer():
    
    try:
        
        data=to_LlmDoc()
        answer=SimpleAnswer(question=query,docs=data,persona=persona,llm=None)
        response=answer.llm_answer
            
        print("Simple Answer Response")
        print(response)
    except Exception as e:
        print(f"Error generating response: {e}")
        print('No Data Found')



if __name__ == "__main__":
    #asyncio.run(generate_response())
    #openai_response()
    loop = asyncio.get_event_loop()
    # Run the generate_simple_answer coroutine in the current event loop
    loop.run_until_complete(generate_simple_answer())
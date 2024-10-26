import asyncio
import os
import sys
import argparse
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.persona.executor import PersonaGenExecutor
from superpilot.examples.persona.rank_personas import rank_personas_list
def persona():

    query='Top traders of the world'

    #personas=generate_personas(query)
    # print('Personas Type',type(personas))

    # persona_executor = PersonaGenExecutor()

    import asyncio

    #Generating 10 Personas with Multiple Queries

    ai_list = asyncio.run(persona_list_generator(query))

    print('Personas List')
    print(ai_list)



    # #Generating 10 Personas from Prompt
    # persona_executor = PersonaGenExecutor()

    # response=asyncio.run(persona_executor.process_row(query))


    # print('AI Personas')
    # print(response)



async def generate_personas(query):
    process = PersonaGenExecutor()
    objective = f"Create 10 detailed AI agent persona based on the- user_query: {query}"
    response = await (process.process_row(objective))
    #print(response)
    personas=response.content
    personas=personas["personas"]
    print("Number of Personas",len(personas))
    return personas

def generate_agent_response(query):
    url = "http://qa-search-service.co/api/v1/search/query/agents/"
    payload = {"query": query}
    response = requests.post(url, json=payload, timeout=5)
    data = response.json().get("data", [])
    return [item["metadata"] for item in data]



    
def test_persona(query):

    personas=asyncio.run(generate_personas(query))
    print()
    print()
    print()
    print()
    print()
    print()
    print()
    personas=personas["personas"]
    print("Number of Personas",len(personas))
    return personas





if __name__ == "__main__":
    # persona()
    query='Top historical events of the world'
    personas=asyncio.run(generate_personas(query))
    print("Pesonas Generated")

    for i, persona in enumerate(personas, start=1):
        print(f"{i}. {persona['persona_name']}")

    #print(personas[0])
    print()
    
    print("Ranked Personas")

    ranked_personas=rank_personas_list(personas=personas,query=query)
    #print(ranked_personas)
    for i, persona in enumerate(ranked_personas, start=1):
        print(f"{i}. {persona[0]} Score: {persona[1]}")
    #rank_personas_list2(query)
    # for i, persona in enumerate(ranked_personas, start=1):
    #     print(f"{i}. {persona['persona_name']}")
import asyncio
import os
import sys
import argparse
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.persona.executor import PersonaGenExecutor
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
    objective = f"Create 6 detailed AI agent persona based on the- user_query: {query}"
    response = await (process.process_row(objective))
    print(response)
    return response.content
def test_persona():
    asyncio.run(generate_personas('Top inventions of the world'))


if __name__ == "__main__":
    # persona()
    test_persona()
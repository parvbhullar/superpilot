
import os
import sys
import argparse
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.examples.persona.multiple_persona_generator import persona_list_generator
from superpilot.examples.persona.executor import PersonaGenExecutor

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





#print(response)

print('Done,check')
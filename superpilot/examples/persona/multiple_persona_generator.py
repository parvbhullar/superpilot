
from superpilot.examples.persona.executor import PersonaGenExecutor,AIPersona,AIPersonaList,KnowledgeBase
import os
#import openai
import asyncio
#import await


from typing import List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def persona():
    # Set your OpenAI API key from the .env file
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise ValueError("API key not found. Please set it in the .env file.")

    # Initialize ChatOpenAI model with your API key
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key=api_key)

    # Define a prompt template for generating related queries
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template="Given the query: '{query}', generate 9 related queries that explore different perspectives on the topic."
    )

    # Create an LLM chain
    chain = LLMChain(llm=llm, prompt=prompt_template)

def generate_related_queries(query: str) -> List[str]:
    """
    Generate 9 related queries based on the provided query.
    
    Parameters:
    - query: str: The original query to base related queries on.
    
    Returns:
    - List[str]: A list of related queries.
    """
    # Run the LLM chain with the input query
    response = chain.run(query)
    
    # Split the response into individual queries
    related_queries = [q.strip() for q in response.split('\n') if q.strip()]
    related_queries.append(query)
    return related_queries


def to_aipersona(response_data):
    print('In ToAIPerson')
    print()
    print()
    print()
    ai_persona_instance = AIPersona(
    persona_name=response_data['persona_name'],
    handle=response_data['handle'],
    about=response_data['about'],
    tags=response_data['tags'],
    persona=response_data['persona'],
    questions=response_data['questions'],
    knowledge_bases=[KnowledgeBase(**kb) for kb in response_data['knowledge_bases']]
)
    
    return ai_persona_instance
# print('Printing Personas')
# for persona in personas:
#     print(persona)
#     print()

async def persona_list_generator(query):
    ai_list=[]
    queries=generate_related_queries(query)
    print(queries)

    for query in queries:
        await generate_personas(ai_list, query)

    ai_persona_list=AIPersonaList()
    ai_persona_list.PersonaList=ai_list

    print('Persona List Resturned')

    return ai_list


async def generate_personas(query):
    process = PersonaGenExecutor()
    objective = f"Create a detailed AI Pilot config based on the- user_query: {query}"

    response = await (process.process_row(objective))
    print(response)
    return to_aipersona(response.content)


import asyncio
from superpilot.examples.persona.executor import PersonaGenExecutor
#from langchain import LLMPredictor
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI

llm = ChatOpenAI(model_name="gpt-3.5-turbo")



import json
from abc import ABC
from typing import List, Dict, Any

from pydantic import Field

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.configuration.config import get_config
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.planning import LanguageModelClassification
from superpilot.core.planning.settings import PromptStrategyConfiguration
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    OpenAIModelName, SchemaModel,
)
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.solution_qc.prompt import QuestionAnswerAnalysisPrompt
from superpilot.tests.test_env_simple import get_env
from datasets import load_dataset
from tqdm import tqdm



import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

def get_embeddings(sentences):
    model = SentenceTransformer('all-MiniLM-L6-v2')  # You can choose a different model if needed
    return model.encode(sentences)

def calculate_cosine_similarity(arr1, arr2):
    # Validation: Check if either array is empty
    if not arr1 or not arr2:
        return 0

    # Extend the shorter array by duplicating elements
    len1, len2 = len(arr1), len(arr2)
    if len1 < len2:
        arr1 = arr1 * (len2 // len1) + arr1[:len2 % len1]
    elif len2 < len1:
        arr2 = arr2 * (len1 // len2) + arr2[:len1 % len2]

    # Get embeddings for both arrays
    embeddings1 = get_embeddings(arr1)
    embeddings2 = get_embeddings(arr2)

    # Calculate cosine similarity
    similarity = cosine_similarity(embeddings1, embeddings2)
    
    # Return the average similarity score
    return np.mean(similarity)













class KnowledgeBase(SchemaModel):
    """
    Model representing a single knowledge base with its relevant data source information.
    """
    name: str = Field(None, description="Name of the knowledge base providing information to the AI persona.")
    datasource: str = Field(None,
                            description="Type and description of the data sources used by this knowledge base to inform the AI persona.")

class Keywords(SchemaModel):
    """
    Class representing the data structure for follow-up questions based on a user query and response.
    """
    keuwords: List[str] = Field(None, 
                                          description="List of keywords to follow revolving around query")


class PersonaGenPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT = """
    You are tasked with creating 5 one words keywords based on the given user_query. 
    These keywords should encourage deeper exploration of the user_query, covering different aspects. 
    Each keyword should have a relevancy  which will  be relevant to user_query.
    Please generate the following fields in a list of strings format:
    
    """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        {task_objective}
    """

    DEFAULT_PARSER_SCHEMA = Keywords.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.examples.persona.executor.PersonaGenPrompt",
        ),
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification = default_configuration.model_classification,
        system_prompt: str = default_configuration.system_prompt,
        user_prompt_template: str = default_configuration.user_prompt_template,
        parser_schema: Any = None,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._parser_schema = parser_schema
        print("parser_schema", parser_schema)

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification


class KeywordsGenExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    config = get_config()
    env = get_env({})

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.persona_pilot = SimpleTaskPilot.create(
            PersonaGenPrompt.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_O_MINI,
            fast_model_name=OpenAIModelName.GPT4_O_MINI,
        )

    PROMPT_TEMPLATE = """
    ---------------------
    Question: {question}
    ----------------------
    Answer: {solution}
    ----------------------
    SOP excel sheet: {sop}
    _______________________
    Task: Perform a question answer analysis based on the SOP
    """

    async def process_row(self, objective):
        response = await self.persona_pilot.execute(objective)
        #print(response.content)
        return response

    async def execute(self, query:str):
        # Load the dataset
        
            objective = f"Create a 5 one word keywords based on {query} revolving around context of {query}"
            response = await self.process_row(objective)
            return(response.content)
        #         for col_name, col_value in response.content.items():
        #             o[col_name] = col_value
        #         out.write(json.dumps(o, ensure_ascii=False) + '\n')
        #         count += 1

        # print(f"Outputted the results to: {args.output_path}")
        #return args.output_path, count

    async def run(self, *args, **kwargs):
        query = kwargs.get('query', '')
        response = kwargs.get('response', '')
        
        if not query or not response:
            raise ValueError("Both 'query' and 'response' must be provided.")
        
        # Call the execute method to process the query and response
        result = await self.execute(query)
        return result






async def generate_keyword_scores(query):
    # Initialize your language model predictor here
      # Replace with your actual LLM configuration
    keywords=KeywordsGenExecutor()
    keywords_response=await keywords.execute(query=query)
    print(keywords_response)
    return(keywords_response)





def calculate_relevancy(persona, query, keywords):
    relevancy_score = 0

    # Check for keywords in persona's tags, questions, and description
    for key, score in keywords.items():
        if key in persona['tags']:
            relevancy_score += score
        # if any(key in question for question in persona['questions']):
        #     relevancy_score += score
        if key in persona['about'].lower() or key in persona['persona'].lower():
            relevancy_score += score

    # Validate if the tags in persona are present in keywords, if not, add them with score 1
    for tag in persona['tags']:
        if tag.lower() not in keywords:
            keywords[tag.lower()] = 1  # Add the missing tag to keywords with a score of 1
            relevancy_score += 1  # Add score for the newly added tag

    return relevancy_score


async def generate_personas(query):
    process = PersonaGenExecutor()
    objective = f"Create 10 detailed AI agent persona based on the- user_query: {query}"
    response = await (process.process_row(objective))
    #print(response)
    return response.content

import openai
# from datasets import Dataset 
# from ragas.metrics import answer_relevancy,faithfulness, answer_correctness
# from ragas import evaluate
def generate_tags(input_text, model="gpt-3.5-turbo", num_tags=3):
    try:
        print()
        keyword=asyncio.run(generate_keyword_scores(input_text))
        print("Keywords",keyword)
        print()
        tags=keyword['keuwords']
        return tags
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return []



# def filtered_agents(query,personas):
#     result=[]
#     answers='history'
#     for persona in personas:
#         data_samples={
#                 'question':[query],
#                 'answer':' '.join(map(str, answers)),
#                 'ground_truth':' '.join(map(str, persona["tags"])),
#             }
#         dataset = Dataset.from_dict(data_samples)
#         score = evaluate(dataset,metrics=[answer_correctness])
#         sc=score.to_pandas()
#         sc['metrics']='correctness'
#         result.append(sc)
#         #print(truth[0])
#         print(persona["name"],sc['answer_correctness'].iloc(0))

def filtered_agents(query, personas):
    tags = generate_tags(query)
    ranked_personas = []

    for persona in personas:
        cos = calculate_cosine_similarity(persona["tags"], tags)
        print(cos)
        # Only append if cosine similarity is greater than 0
        if cos > 0.20:
            ranked_personas.append((persona, cos))

    # Sort the ranked_personas list by cosine similarity in descending order
    ranked_personas.sort(key=lambda x: x[1], reverse=True)

    # Extract only the persona objects in sorted order
    ranked_persona_list = [persona[0] for persona in ranked_personas]

    return ranked_persona_list

import requests
def generate_agent_response(query):
    url = "http://qa-search-service.co/api/v1/search/query/agents/"
    payload = {
        "query": query,
        }
    response = requests.post(url, json=payload,timeout=5)
    result=response.json()
    data=result["data"]
    agents=[item["metadata"] for item in data]

    return agents




def rank_personas(query:str):
    #personas=asyncio.run(generate_personas(query))
    personas=generate_agent_response(query)
    
    ranked_personas=filtered_agents(query=query,personas=personas)
    print("PERSONAS")
    #personas=personas['personas']
    print("Number of Personas",len(personas))
    print("Tags")
    for i, persona in enumerate(personas, start=1):
        print(f"{i}.{persona['persona_name']} - {persona['tags']}")

    print()


    # keywords = {
    # 'inventions': 5,
    # 'history': 4,
    # 'technology': 3,
    # 'innovation': 3,
    # 'impact': 2,
    # 'future': 2,
    # 'events':2,
    # 'economics': 2,
    # 'society': 1,
    # 'environment': 1,
    # 'science': 3,
    # 'analysis':2,
    # 'research':2,
    # 'data':3,
    # 'politics':2,
    # }
    

    #query = "Top inventions of the world"

# Rank personas by relevancy score, updating keywords dynamically if necessary
    #ranked_personas = sorted(personas, key=lambda p: calculate_relevancy(p, query, keywords), reverse=True)

    # Display ranked personas from top to bottom
    for i, persona in enumerate(ranked_personas, start=1):
        print(f"{i}. {persona['persona_name']}")

    # Display updated keywords for reference
    # print("\nUpdated Keywords:")
    # for key, score in keywords.items():
    #     print(f"{key}: {score}")

    return ranked_personas
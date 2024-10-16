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


class KnowledgeBase(SchemaModel):
    """
    Model representing a single knowledge base with its relevant data source information.
    """
    name: str = Field(None, description="Name of the knowledge base providing information to the AI persona.")
    datasource: str = Field(None,
                            description="Type and description of the data sources used by this knowledge base to inform the AI persona.")

class FollowUpQuestions(SchemaModel):
    """
    Class representing the data structure for follow-up questions based on a user query and response.
    """
    followup_questions: List[str] = Field(None, 
                                          description="List of questions to follow revolving around query")


class PersonaGenPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT = """
    You are tasked with creating 5 detailed follow-up questions based on the given user_query and response. 
    These follow-up questions should encourage deeper exploration of the topic, covering different aspects, challenges, and perspectives that could lead to further clarification or insights. 
    Each question should be engaging, relevant, and stimulate thoughtful conversation.
    Please generate the following fields in a structured list format:
    Every response should be in string only with each response not more than 12 words. 
    """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        {task_objective}
    """

    DEFAULT_PARSER_SCHEMA = FollowUpQuestions.function_schema()

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


class FollowUpGenExecutor(BaseExecutor):
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
        print(response.content)
        return response

    async def execute(self, query:str,response:str):
        # Load the dataset
        
            objective = f"Create a 5 follow up questions based on {query} and {response} revolving around context of both should not be more than 12 words each"
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
        result = await self.execute(query, response)
        return result

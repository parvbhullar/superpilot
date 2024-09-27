from abc import ABC
from typing import List, Dict

from pydantic import Field

import pandas as pd

from superpilot.core.configuration.config import get_config
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.planning import LanguageModelClassification
from superpilot.core.planning.settings import PromptStrategyConfiguration
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    OpenAIModelName, SchemaModel,
)
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.solution_qc.prompt import QuestionAnswerAnalysisPrompt
from superpilot.tests.test_env_simple import get_env


class KnowledgeBase(SchemaModel):
    """
    Model representing a single knowledge base with its relevant data source information.
    """
    name: str = Field(None, description="Name of the knowledge base providing information to the AI persona.")
    datasource: str = Field(None,
                            description="Type and description of the data sources used by this knowledge base to inform the AI persona.")


class AIPersona(SchemaModel):
    """
    Model representing an AI persona with details about its identity, background, and knowledge base.
    """

    persona_name: str = Field(None, description="The name of the AI persona, representing its identity.")
    handle: str = Field(None,
                        description="Unique identifier for the AI persona, typically in the format 'name-of-ais'.")
    # about: str = Field(None,
    #                    description="Description of the AI persona, based on the 'input_persona' from the dataset, explaining its purpose and area of expertise.")
    tags: List[str] = Field(None,
                            description="Tags associated with the AI persona, providing keywords based on its persona or areas of expertise.")

    # persona: str = Field(None,
    #                      description="Synthesized text from the dataset, providing a more detailed explanation of the AI persona's purpose, expertise, and activities.")
    questions: List[str] = Field(None,
                                 description="A set of 4 key questions derived from the synthesized text, meant to help users understand and engage with the AI persona.")

    knowledge_bases: List[KnowledgeBase] = Field(None, description="""
        A list of knowledge bases this AI persona relies on for expertise.
        Each knowledge base includes the name of the knowledge base and the data sources it draws from.
    """)



class PersonaGenPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT = """
       You are tasked with creating a detailed AI Pilot config based on the persona_tagline and persona. Please generate the following fields in a structured format:

        1. **Name**: The name of the AI persona, representing its identity or role.
           
        2. **Handle**: A unique identifier for this AI persona, in the format 'name-of-ais'.
        
        4. **Tags**: Keywords or tags related to the persona's expertise and characteristics. These should be derived from the input persona. Provide 3-5 tags.

        6. **Questions**: Generate 4 questions that could help users interact with and better understand the AI persona, based on its synthesized text and expertise.
        
        7. **Knowledge Bases**: List at least one knowledge base that this persona draws information from. Each knowledge base should have:  
           - **Name**: The name of the knowledge base.  
           - **Data Source**: A brief description of the type of data or resources that this knowledge base uses to provide information.
        

    """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        {task_objective}
    """

    DEFAULT_PARSER_SCHEMA = AIPersona.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification = default_configuration.model_classification,
        system_prompt: str = default_configuration.system_prompt,
        user_prompt_template: str = default_configuration.user_prompt_template,
        parser_schema: Dict = None,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._parser_schema = parser_schema

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def parse_response_content(
        self,
        response_content: dict,
    ) -> dict:
        """Parse the actual text response from the objective model.

        Args:
            response_content: The raw response content from the objective model.

        Returns:
            The parsed response.

        """
        # print(response_content)
        parsed_response = json_loads(response_content["function_call"]["arguments"])
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response

class PersonaGenExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    config = get_config()
    env = get_env({})

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.persona_pilot = SimpleTaskPilot.create(
            PersonaGenPrompt.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4,
            fast_model_name=OpenAIModelName.GPT3,
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

    async def process_row(self, row):
        objective = f"Create a detailed AI Pilot config based on the- persona_tagline: {row['input_persona']['text']}, persona: {row['synthesized_text']['text']}"
        response = await self.persona_pilot.execute(objective)
        print(response.content)
        return response

    async def execute(self, dataset):
        df = pd.DataFrame(dataset)
        output_file = "output.xlsx"
        count = 0
        for index, row in df.iterrows():
            response = await self.process_row(row)
            for col_name, col_value in response.content.items():
                df.at[index, col_name] = col_value
            if count > 10:
                break
            count += 1

        df.to_excel(output_file, index=False)
        return output_file, len(df)

    async def run(self, dataset):
        output_file, count = await self.execute(dataset)
        return {
            "message": f"file successfully processed",
            "processed_count": count,
        }

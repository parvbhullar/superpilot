import json
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
from datasets import load_dataset
from tqdm import tqdm


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
    about: str = Field(None,
                       description="Description of the AI persona, based on the 'input_persona' from the dataset, explaining its purpose and area of expertise.")
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
        Every response should be in json only. 
        - persona_name: The name of the AI persona, representing its identity.
        - handle: Unique identifier for the AI persona, typically in the format 'name-of-ais'.
        - about: Description of the AI persona, explaining its purpose and area of expertise.
        - tags: Tags associated with the AI persona, providing keywords based on its persona or areas of expertise.
        - questions: A set of 6 key questions derived from the synthesized text, meant to help users understand and engage with the AI persona.
        - knowledge_bases: A list of knowledge bases this AI persona relies on for expertise. Each knowledge base includes the name of the knowledge base and the data sources it draws from.
        

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
        print("parser_schema", parser_schema)

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification


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

    async def execute(self, args):
        # Load the dataset
        persona_dataset = load_dataset("proj-persona/PersonaHub", data_files=f"{args.template}.jsonl")['train']
        if args.sample_size > 0:
            persona_dataset = persona_dataset[:args.sample_size]
        print(persona_dataset)
        print(f"Total number of input {args.template}: {len(persona_dataset['input persona'])}")
        count = 0
        with open(args.output_path, "w") as out:
            for persona in tqdm(persona_dataset['input persona']):
                persona = persona.strip()
                print(f"Processing persona: {persona}")
                o = {"input_persona": persona, "synthesized_text": persona_dataset['synthesized text'][count]}
                objective = f"Create a detailed AI Pilot config based on the- persona_tagline: {o['input_persona']}, persona: {o['synthesized_text']}"
                response = await self.process_row(objective)
                print(response.content)
                for col_name, col_value in response.content.get("content").items():
                    o[col_name] = col_value
                out.write(json.dumps(o, ensure_ascii=False) + '\n')
                count += 1

        print(f"Outputted the results to: {args.output_path}")
        return args.output_path, count

    async def run(self, args):
        output_file, count = await self.execute(args)
        return {
            "message": f"file successfully processed - {output_file}",
            "processed_count": count,
        }

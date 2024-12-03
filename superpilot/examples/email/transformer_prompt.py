from abc import ABC

from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.strategies.simple import SimplePrompt

from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
    SchemaModel,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict, Optional
import enum

from pydantic import Field
from typing import List


class Document(SchemaModel):
    """
    Class representing the data structure for document-related information.
    """
    document_number: str = Field(..., description="Document Number")
    document_date: str = Field(..., description="Document Date in format DD-MM-YYYY")


class DataList(SchemaModel):
    """
    Container class representing a tree of questions to ask a question answer system.
    and its dependencies. Make sure every question is in the tree, and every question is asked only once.
    """

    documents: List[Document] = Field(
        ..., description="List of gstr documents/rows to be processed"
    )


class TransformerPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT = """
        you are a Data transformer expert. You need to analyze the data and provide the correct data & their respective fields such as status.

        Examples :-
        

        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        Content: {task_objective}

        -----
        Please use the above input as the content for the json generation.
        """

    DEFAULT_PARSER_SCHEMA = DataList.function_schema()

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


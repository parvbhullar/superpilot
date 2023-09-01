import json

from superpilot.core.configuration import SystemConfiguration, UserConfigurable
from superpilot.core.planning.base import PromptStrategy
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
from pydantic import Field
from typing import List, Optional, Union


class BaseContent(SchemaModel):
    """
    Class representing a question and its answer as a list of facts each one should have a soruce.
    each sentence contains a body and a list of sources."""

    content: str = Field(..., description="Response content from the llm model")
    highlights: List[str] = Field(
        ...,
        description="Body of the answer, each fact should be its separate object with a body and a list of sources",
    )


class SuperPrompt(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = (
        "Your job is to respond to a user-defined query by answering the question, "
        "Or completing the task it could be passing the format and generating the "
        "requested response in given function call model."
    )

    DEFAULT_USER_PROMPT_TEMPLATE = "'{user_objective}'"

    DEFAULT_PARSER = BaseContent

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser=DEFAULT_PARSER,
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification,
        system_prompt: str,
        user_prompt_template: str,
        parser: SchemaModel,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template
        self._parser = parser

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(self, user_objective: str = "", **kwargs) -> LanguageModelPrompt:
        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message,
        )
        user_message = LanguageModelMessage(
            role=MessageRole.USER,
            content=self._user_prompt_template.format(
                user_objective=user_objective,
            ),
        )
        parser_function = LanguageModelFunction(
            json_schema=self._parser.schema,
        )
        prompt = LanguageModelPrompt(
            messages=[system_message, user_message],
            functions=[parser_function],
            # TODO
            tokens_used=0,
        )
        return prompt

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
        # parsed_response = json_loads(response_content["function_call"]["arguments"])
        parsed_response = self._parser.from_response(response_content)
        return parsed_response

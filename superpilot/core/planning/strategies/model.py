from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    LanguageModelMessage,
    MessageRole,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration


class ModelPromptStrategy(PromptStrategy):
    def __init__(self, *args, **kwargs):
        pass

    @property
    def model_classification(self) -> LanguageModelClassification:
        pass

    def build_prompt(self, **kwargs) -> LanguageModelPrompt:
        message_history = kwargs.pop("message_history", [])
        prompt_message_history = []
        for message in message_history:
            prompt_message_history.append(
                LanguageModelMessage(role=message.role, content=message.content)
            )
        user_input = kwargs.pop("user_input", "")
        user_message = LanguageModelMessage(
            role=MessageRole.USER,
            content=user_input,
        )
        prompt = LanguageModelPrompt(messages=[*prompt_message_history, user_message])
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
        if "function_call" in response_content:
            parsed_response = json_loads(response_content["function_call"]["arguments"])
        else:
            parsed_response = response_content
        return parsed_response

    def get_config(self) -> PromptStrategyConfiguration:
        return PromptStrategyConfiguration(
            model_classification=self._model_classification,
            system_prompt=self._system_prompt_message,
            user_prompt_template=self._user_prompt_template,
            parser_schema=self._parser_schema,
        )

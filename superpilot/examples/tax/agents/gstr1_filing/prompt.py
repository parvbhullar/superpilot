from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.resource.model_providers import (
    LanguageModelMessage,
    MessageRole,
)


class Gstr1DataTransformPromptStrategy(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = """
    """

    DEFAULT_USER_PROMPT_TEMPLATE = """
    """

    def __init__(
        self,
        model_classification: LanguageModelClassification = LanguageModelClassification.SMART_MODEL,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        user_prompt_template: str = DEFAULT_USER_PROMPT_TEMPLATE,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(self, content: str, **kwargs) -> LanguageModelPrompt:
        # Define a system message to set the context
        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message,
        )

        # Create a user message with the provided content
        user_message = LanguageModelMessage(
            role=MessageRole.USER,
            content=self._user_prompt_template.format(content=content),
        )

        # Construct the prompt
        prompt = LanguageModelPrompt(
            messages=[system_message, user_message],
            functions=[],
            tokens_used=0,
        )
        return prompt

    def parse_response_content(self, response_content: dict) -> str:
        """Parse the actual text response from the objective model.

        Args:
            response_content: The raw response content from the objective model.

        Returns:
            The parsed Markdown content as a string.

        """
        parsed_response = response_content.get("choices", [{}])[0].get("text", "")
        return parsed_response

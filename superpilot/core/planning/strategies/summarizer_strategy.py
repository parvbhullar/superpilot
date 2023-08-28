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
)


class SummarizerConfiguration(SystemConfiguration):
    model_classification: LanguageModelClassification = UserConfigurable()
    system_prompt: str = UserConfigurable()
    user_prompt_template: str = UserConfigurable()
    # summarizer_function: dict = UserConfigurable()


class SummarizerStrategy(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = (
        "Act as a research analyst who is specialized in summarizing complex information from various sources. "
        "Your goal is to condense a long piece of text, possibly spanning multiple documents or web pages, "
        "into a concise summary that retains the essential information. You must take care to accurately "
        "represent the original content, maintain the intended meaning, and cite the sources from which the "
        "information was derived. Your task will involve carefully reading and analyzing the text, identifying "
        "the key points, organizing them in a coherent manner, and then writing a brief summary that is easily "
        "understandable. Consider using paraphrasing techniques to avoid plagiarism, and make sure to include "
        "proper citations for all sources used. Remember, your summary must be informative and free from personal bias,"
        " reflecting only the facts and insights presented in the original text."
    )

    DEFAULT_USER_PROMPT_TEMPLATE = (
        "Summaries: {content} \n\n"
        "Using the above information, answer the following question or topic: {question} in a detailed response --"
        "The response should focus on the answer to the question, should be well structured, informative, "
        "in depth, with facts, stats and numbers if available, a minimum of 500 words and with markdown syntax and apa format. "
        "if the question cannot be answered using the text, simply summarize the text in depth. "
        "You MUST determine your own concrete and valid opinion based on the information found. Do NOT deter to general and meaningless conclusions."
        "Write all source urls at the end of the response in apa format"
    )

    DEFAULT_SUMMARIZER_FUNCTION = {
        "name": "summarizer_function",
        "description": "Creates a set of tasks that forms the initial plan for an autonomous pilot.",
    }

    default_configuration = SummarizerConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification,
        system_prompt: str,
        user_prompt_template: str,
    ):
        self._model_classification = model_classification
        self._system_prompt_message = system_prompt
        self._user_prompt_template = user_prompt_template

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(self, content: str = "", question: str = "", **kwargs) -> LanguageModelPrompt:
        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message,
        )
        content = content.replace("\n", " ")
        user_message = LanguageModelMessage(
            role=MessageRole.USER,
            content=self._user_prompt_template.format(
                content=content, question=question
            ),
        )

        prompt = LanguageModelPrompt(
            messages=[system_message, user_message],
            functions=[],
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
        parsed_response = json_loads(response_content["function_call"]["arguments"])
        return parsed_response

from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.schema import LanguageModelClassification
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict


class TopicsPromptHN(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = """
        You are teacher guide creator. You need to create teacher guide for the given content to be taught by the teacher.
        Your language should be simple and easy to understand.
        You should reply in Hindi language and a minimum of 200 words and with markdown syntax and apa format.

        Format Instructions:
        1. Topics to be covered in given chapter(table format)
        2. What we will learn from the topic or chapter (bullets or table format)
        3. Learning outcomes after completing the chapter (bullets or table format)

        Example:
        Name of the Chapter
        हम इस अध्याय में निम्नलिखित विषयों को शामिल करेंगे:
        इस विषय में हम क्या सीखेंगे-
            सीखने के परिणाम
            अध्याय के अंत में, छात्रों को निम्नलिखित विषयों के बारे में जानने में सक्षम होना चाहिए
        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        Chapter:
        {context}

        task:{task_objective}
        """

    DEFAULT_PARSER_SCHEMA = None  # Question.function_schema()

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
        if "function_call" in response_content:
            parsed_response = json_loads(response_content["function_call"]["arguments"])
        else:
            parsed_response = response_content
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response

    def get_config(self) -> PromptStrategyConfiguration:
        return PromptStrategyConfiguration(
            model_classification=self._model_classification,
            system_prompt=self._system_prompt_message,
            user_prompt_template=self._user_prompt_template,
            parser_schema=self._parser_schema,
            location=PluginLocation(
                storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                storage_route=f"{__name__}.{self.__class__.__name__}",
            ),
        )

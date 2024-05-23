# flake8: noqa
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict
from superpilot.core.resource.model_providers.schema import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
)


class AnswerCategorizerPrompt(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = """
        You are Answer Categorizer whose work to categorize the the answer / query into the sets, based upon the content.
        categorize the answer / query into array of dict, where dict contains the below keys

        type: string
        text: string

        here type is the categorized type of the answer / query, and text is the text of the answer / query.

        type can be any of the following:
        a. text
        b. code
        c. latex
        d. table
        e. image
        etc.


        Example:
        Query:
        The formula to calculate the income tax on birr \( x \), where \( x \) falls in the interval [5250, 7800], is:

        \[
        \textTax = 0.10 \times (x - 5250)
        \]

        Explanation:
        - For income up to 5250 birr, no tax is applied, so the tax is 0.
        - For income above 5250 birr and up to 7800 birr, a 10% tax rate is applied to the amount exceeding 5250 birr.

        Given that \( x \) is within the interval [5250, 7800], the tax calculation simplifies to:

        \[
        \textTax = 0.10 \times (x - 5250)
        \]

        This formula directly applies the 10% tax rate to the portion of income that exceeds 5250 birr.

        Response:
        [
            {
                'type': 'text',
                'text': 'The formula to calculate the income tax on birr \\( x \\), where \\( x \\) falls in the interval [5250, 7800], is:'
            },
            {
                'type': 'latex',
                'text': '\\[ \\textTax = 0.10 \\times (x - 5250) \\]'
            },
            {
                'type': 'text',
                'text': 'Explanation: \n- For income up to 5250 birr, no tax is applied, so the tax is 0.\n- For income above 5250 birr and up to 7800 birr, a 10% tax rate is applied to the amount exceeding 5250 birr. \n Given that \\( x \\) is within the interval [5250, 7800], the tax calculation simplifies to:'
            },
            {
                'type': 'latex',
                'text': '\\[ \\textTax = 0.10 \\times (x - 5250) \\]'
            },
            {
                'type': 'text',
                'text': 'This formula directly applies the 10% tax rate to the portion of income that exceeds 5250 birr.'
            }
        ]
        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        Query:{task_objective}
        Please provide the answer / query in the above format in JSON
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
        try:
            response_content = json_loads(
                response_content["content"].lstrip("Response:")
            )
        except Exception as ex:
            print(response_content["content"].lstrip("Response:"))
            pass
        if isinstance(response_content, list):
            response_content = {"content": response_content}
        return response_content

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

    def build_prompt(self, **kwargs) -> LanguageModelPrompt:
        template_kwargs = self.get_template_kwargs(kwargs)

        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message,
        )
        user_message = LanguageModelMessage(
            role=MessageRole.USER,
            content=self._user_prompt_template.format(**template_kwargs),
        )

        functions = []
        if self._parser_schema is not None:
            parser_function = LanguageModelFunction(
                json_schema=self._parser_schema,
            )
            functions.append(parser_function)
        prompt = LanguageModelPrompt(
            messages=[system_message, user_message],
            functions=functions,
            function_call=None if not functions else functions[0],
            tokens_used=0,
        )
        return prompt

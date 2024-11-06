from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict

from superpilot.examples.ed_tech.question_solver import QuestionSolverPrompt


class DescribeQFigurePrompt(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = """
        You are a question extractor that Extract the question with latex given in the image also explaining 
        given figures or diagrams but do not answer the question.

        Instructions:
        - Only return the question with latex code.
        - Don't respond in json format, only text format is allowed as described below

       Example:
        What is the theoretical yield of compound ( C ), in grams, when ( 67.5 g ) of compound ( A ) 
        are allowed to react with ( 39.1 g ) of compound ( B ) in the presence of a catalytic amount of sulfuric acid?
        Shown in Figure: The image shows chemical structures of three compounds labeled A, B, and C. There's an arrow from A and B leading to C implying 
            a chemical reaction. Above the arrow, "H2SO4" is written along with "(cat amt)," indicating that sulfuric acid is used 
            as a catalyst in this reaction. Compound A is a benzene ring with an attached formyl group (–CHO), more specifically, 
            it is benzaldehyde. Compound B is a straight-chain hydrocarbon with an alcohol group (–OH) at the end of the chain, this is 1-pentanol. 
            Compound C, the product of the reaction, is an ester formed by the reaction between A and B under catalytic conditions, more specifically, 
            it is pentyl benzoate.
    
        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        conversation:
        {context}
        Extract the question from image with figure explanation. 
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

    # @classmethod
    # def factory(
    #     cls,
    #     system_prompt=None,
    #     user_prompt_template=None,
    #     parser=None,
    #     model_classification=None,
    # ) -> "QuestionSolverPrompt":
    #     config = cls.default_configuration.dict()
    #     if model_classification:
    #         config["model_classification"] = model_classification
    #     if system_prompt:
    #         config["system_prompt"] = system_prompt
    #     if user_prompt_template:
    #         config["user_prompt_template"] = user_prompt_template
    #     if parser:
    #         config["parser_schema"] = parser
    #     config.pop("location", None)
    #     return cls(**config)

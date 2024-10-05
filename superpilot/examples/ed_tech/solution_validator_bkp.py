# flake8: noqa: F401
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


class SolutionValidatorPrompt(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = """
        Solve question based on conversation of user and assistant for given Question, also fix the inaccuracies in solution:
        Solve the question in 3-4 steps, brief about question, step by step solution(use latex) and explanation of each step.
        make sure to answer the question on given conversation. Follow the below instructions.

        Instructions:
        - Solve the problem step by step (do not over-divide the steps).
        - Solve each and every equation in the solution.
        - Write a complete solution without loosing symbols, equations, options, tables etc.
        - Write solution and equations in correct latex format.
        - Avoid use of personal and user conversation, we, they, you, I in the solution at all.
        - Please do not mention here is the formatted solution or here is the formatted answer, format answer as teacher answer a question.
        - Don't respond in json format, only text format is allowed as described below

        Step1:
            Brief with latex code
            Explanation
        Step2:
            Brief with latex code
            Explanation

        Final solution:

        Example:
        Step1:
        Marked price is known as the original price of the product which is decided by the manufacturer on the basis of the cost incurred to produce the product.
        It is given that the saving is of $180 on a laptop by getting 10% discount
        To find the original cost of the laptop.

        Explanation:
        Discount is the price equal to the difference between the original price and the amount paid by the customer.

        Step2:
        Discount is offered by the shopkeeper to the customers to increase the sales in lean seasons.
        Consider the original cost of the laptop be x
        Discount percentage = 10%
        Discount amount = 180
        Relation between percentage, amount and original value:
        Percentage * Original value = Discount amount
        Substituting the values:
        10% of x = 180
        0.1x = 180
        x = 180/0.1 = $1800

        Explanation:
        To find the original cost of the laptop, multiply the discount percentage by original price and equate it to the discounted price.

        Final answer:
        The original cost of the laptop was $boxed $1800$.

        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        conversation:
        {context}

        question:{task_objective}
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

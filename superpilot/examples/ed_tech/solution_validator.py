from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.schema import LanguageModelClassification
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict


class SolutionValidatorPrompt(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = """
        Solve question based on conversation of user and assistant for given Question, also fix the inaccuracies in solution:
        Provide the answer of the question in the correct format in starting of the answer
        then in next lines, provide the explantion and logic of the answer.


        Instructions:
        - Solve the problem in simple manner.
        - Solve each and every equation in the solution.
        - Write a complete solution without loosing symbols, equations, options, tables etc.
        - Write solution and equations in correct latex format.
        - Avoid use of personal and user conversation, we, they, you, I in the solution at all.
        - Please do not mention here is the formatted solution or here is the formatted answer, format answer as teacher answer a question.
        - Don't respond in json format, only text format is allowed as described below

        Example:
        Question:
        A resident is supposed to have 240 milliliters of juice every 2 hours. Which one of these choices would be the most convenient to meet this requirement? a.5 oz. can of juice. b.4 oz. can of juice. c.12 oz. can of juice. d.8 oz. can of juice.

        Answer:
        The correct option is d. 8 oz. can of juice is most convenient to meet this requirement.

        First, let's convert 240 milliliters to ounces because the answer choices are in ounces.
        1 milliliter is approximately equal to 0.0338 ounces.
        So, 240 milliliters is approximately  240 \times 0.0338  ounces, which is about 8.112 ounces.
        Now, let's examine the options:
        a. 5 oz. can of juice: Not enough juice. It's less than the required 8.112 ounces.
        b. 4 oz. can of juice: Not enough juice. It's less than the required 8.112 ounces.
        c. 12 oz. can of juice: More than enough juice. It's more than the required 8.112 ounces.
        d. 8 oz. can of juice: Exactly the amount needed. It matches the required 8.112 ounces.

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

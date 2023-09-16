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
from typing import Dict


class BasePromptModel(SchemaModel):
    """
    This class serves as a data model for the response of the Content Analysis system

    Attributes:
    - content (str): The generated content or response.
    - status (str): Status of the content (Complete, Cannot be Fixed, Spam).
    - reason (str, optional): Additional information or reason if needed.
    """

    content: str
    status: str
    reason: str = None


class QuestionIdentifierPrompt(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = """
        Act as the Content Correct Analysis, who's work is to correct the content based on the provided content.
        What you need to do :-
        - Do not change the lanaguage of the content.
        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        Input: {task_objective}

        Please use the above input as the content for the content correct analysis.
        You need to analyze the content & provide the correct content & their respective fields such as status.

        Status can be ENUM.
            Complete --> content can be correct.
            Cannot be Fixed --> content has unnecessary info, and can't be correct.
            Spam --> Invalid content / Meaningless content

        If Status is not Complete, then also provide the reason.

        Below the some Examples.
        1.
            Input: This climate diagram depicts ________. a. a tropical biome b. a very dry environment c. a typical boreal forest biome d. a biome with plentiful moisture e. a biome whose plants experience freeze stress for several months of the year

            Output:
            content - This climate diagram depicts ________.
            (A) a tropical biome
            (B) a very dry environment
            (C) a typical boreal forest biome
            (D) a biome with plentiful moisture
            (E) a biome whose plants experience freeze stress for several months of the year.

            status -> Complete

        2.
            Input: In "Highlander II: The Quickening", we learn that the mysterious Immortals are actually aliens originating from the planet Zeist, a world that is referenced throughout the remainder of the Highlander series, but never actually shown.

            Output:
            content - Cannot be Fixed.
            status -> Cannot be Fixed
            reason -> Not an educational question.
        """

    DEFAULT_PARSER_SCHEMA = BasePromptModel.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.FAST_MODEL,
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

    def build_prompt(self, task_objective: str, **kwargs) -> LanguageModelPrompt:
        template_kwargs = self.get_template_kwargs(task_objective, kwargs)
        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message.format(**template_kwargs),
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
            # TODO
            tokens_used=0,
        )
        return prompt

    def get_template_kwargs(self, task_objective, kwargs):
        template_kwargs = {
            "task_objective": task_objective,
            "cycle_count": 0,
            "action_history": "",
            "additional_info": "",
            "user_input": "",
            "acceptance_criteria": "",
        }
        # Update default kwargs with any provided kwargs
        template_kwargs.update(kwargs)
        return template_kwargs

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
        )

    @classmethod
    def factory(
        cls,
        system_prompt=None,
        user_prompt_template=None,
        parser=None,
        model_classification=None,
    ) -> "QuestionIdentifierPrompt":
        config = cls.default_configuration.dict()
        if model_classification:
            config["model_classification"] = model_classification
        if system_prompt:
            config["system_prompt"] = system_prompt
        if user_prompt_template:
            config["user_prompt_template"] = user_prompt_template
        if parser:
            config["parser_schema"] = parser
        return cls(**config)

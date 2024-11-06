from abc import ABC
from typing import Dict

from pydantic import Field

from superpilot.core.planning.schema import (
    LanguageModelClassification,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    SchemaModel,
)


class QuestionAnswerAnalysis(SchemaModel):
    """
    analysis of question answer
    """
    overall_score:  float = Field(None, description="overall score out of 5")
    overall_comment: str = Field(None, description="overall comment")
    accuracy_rating: int = Field(None, description="accuracy rating out of 5")
    accuracy_problems: str = Field(None, description="accuracy problems")
    concept_rating: int = Field(None, description="concept rating out of 5")
    concept_problems: str = Field(None, description="concept problems")
    explanation_rating: int = Field(None, description="explaination rating out of 5")
    explanation_problems: str = Field(None, description="explaination problems")
    structure_rating: int = Field(None, description="structure rating out of 5")
    structure_problems: str = Field(None, description="structure problems")
    ansguideline_rating: int = Field(None, description="ansguideline rating out of 5")
    ansguideline_problems: str = Field(None, description="ansguideline problems")


class QuestionAnswerAnalysisPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT = """
       You are expert at question answer analysis based on some System of procedures.
    """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        {task_objective}
    """

    DEFAULT_PARSER_SCHEMA = QuestionAnswerAnalysis.function_schema()

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
        # print(response_content)
        parsed_response = json_loads(response_content["function_call"]["arguments"])
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response


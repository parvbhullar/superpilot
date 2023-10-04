from superpilot.core.planning.base import PromptStrategy
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
    SchemaModel,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict
import enum

from pydantic import Field
from typing import List


class QuestionStatus(str, enum.Enum):
    Complete = "complete"
    Incomplete = "incomplete"
    Spam = "spam"
    Cannot_Be_Fixed = "cannot_be_fixed"


class QuestionSubject(str, enum.Enum):
    NotSure = "not_sure"
    Business = "business"
    English = "english"
    Mathematics = "mathematics"
    SocialStudies = "social_studies"
    Health = "health"
    Geography = "geography"
    Biology = "biology"
    Physics = "physics"
    Chemistry = "chemistry"
    ComputersAndTechnology = "computers_and_technology"
    Arts = "arts"
    WorldLanguages = "world_languages"
    Spanish = "spanish"
    French = "french"
    German = "german"
    Medicine = "medicine"
    Law = "law"
    Engineering = "engineering"
    Economics = "economics"


class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    TrueFalse = "true_false"
    FillInBlank = "fill_in_blank"
    FillInTheBlanksWithOptions = "fill_in_the_blanks_with_options"
    MatchTheColumn = "match_the_column"
    ShortAnswer = "short_answer"
    NotSure = "not_sure"


class Question(SchemaModel):
    """
    Class representing a single question in a question answer subquery.
    Can be either a single question or a multi question merge.
    """

    question: str = Field(
        ...,
        description="Complete question from LLM model",
    )
    question_status: QuestionStatus = Field(
        default=QuestionStatus.Incomplete,
        description="Status of the question, whether it is complete or incomplete, cannot be fixed or spam.",
    )
    subject: QuestionSubject = Field(
        default=QuestionSubject.NotSure,
        description="Subject of the question",
    )
    question_type: QuestionType = Field(
        default=QuestionType.MCQ,
        description="Type of the question, whether it is MCQ, True False, Fill in Blank or not.",
    )
    options: List[str] = Field(
        default_factory=list,
        description="List of options for the question, e.g if it is MCQ, then list of options.",
    )


class LatexCodeGenPrompt(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = """
        Your job is to rewriting question to its completed version question with its options.
        make sure to complete the question anyhow. Follow the below instructions.

        Instructions:
        - In case of incomplete question, complete the question including ? mark.
        - Write a complete question without loosing symbols, equations, options, tables etc.
        - Write question and equations in plan text
        - Convert mathml to plain text or signs.
        - Convert latex code to plain text or signs.
        - Latex code should be written in editable plain text like 2/3,2*3,80 (signs in superscript).
        - Do not answer the question, simply provide correct question with right set of options, subject and question_type.
        - If the question is complete, then simply provide the question with its options(if present in text), subject and type.
        - Remove unnecessary brackets, words like Exam Name, Website Name, Page No., Question No., Exercise No., Points, Grade, Marks etc posted in question.
        - If some question mention "given in figure", mark it "cannot be fixed" rather than creating a question out of it
        - If question is incomplete where the options needs to be added, please add the options.
        - If question is with answer then make it fill in blank question, remove the answer from it.
        - If question is incomplete statement then rewrite it to make detailed question.
        - in case of true false question, make sure to add the options as True and False.
        - response should be in JSON format in given keys only(question, question_status, subject, question_type, options).

        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        Question: {task_objective}

        -----
        Please use the above input as the content.

        And return the Response in below Format.

        {output_schema}

        """

    OUTPUT_SCHEMA = Question.function_schema()

    DEFAULT_PARSER_SCHEMA = None  # Question.function_schema()

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
            content=self._user_prompt_template.format(
                **template_kwargs, output_schema=self.OUTPUT_SCHEMA
            ),
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

    @classmethod
    def factory(
        cls,
        system_prompt=None,
        user_prompt_template=None,
        parser=None,
        model_classification=None,
    ) -> "LatexCodeGenPrompt":
        config = cls.default_configuration.dict()
        if model_classification:
            config["model_classification"] = model_classification
        if system_prompt:
            config["system_prompt"] = system_prompt
        if user_prompt_template:
            config["user_prompt_template"] = user_prompt_template
        if parser:
            config["parser_schema"] = parser
        config.pop("location", None)
        return cls(**config)

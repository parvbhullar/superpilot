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
import enum
import asyncio

from pydantic import Field
from typing import List, Optional


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
        description="Fixed and formatted question from the passed content in the query.",
    )
    comment: str = Field(
        ...,
        description="User comment/reason for the question, in case of spam or cannot be fixed.",
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


class QuestionIdentifierPrompt(PromptStrategy):

    DEFAULT_SYSTEM_PROMPT = """
        You are a world class query correction algorithm capable of fixing questions into its corrected version of 
        question and its options.
        Do not answer the question, simply provide correct question with right set of options, subject and category.
        
        Instructions :-
        - Do not change the language of the content
        - Do not generate options if not present in the content.
        - Fix question format in correct format only if it is must e.g. Line Break missing.
        - Generate question if content is an answer - generate question is that case.
        - Correct Spelling, Capital and small letter mistake if any
        - Correct Punctuation errors
        - Fix Subscript/Superscript missing or errors in case of Maths, Chemistry, Physics etc.
        - Incomplete question, options missing - Complete the question
        - Remove unnecessary words like Exam Name, Website Name, Page No., Question No., Exercise No., Points, Grade, Marks etc posted in question.
        - Question not making any sense can be marked as can not be fixed as status.
        - Fix Numbers, equation etc in latex, or math format missing.
        - Only mark question incomplete if you are changing any content in the question, even slight change in the content.
        
        Instructions :-
        - Do not change the data and values, only generate or complete question.
        - Do not generate options if not present in the content.
        - Fix question format in correct format only if it is must e.g. Line Break missing.
        - Generate question if content is an answer - generate question in that case.
        - Correct Spelling, Capital and small letter mistake if any
        - Correct Punctuation errors
        - Remove html tags from the content
        - Fix Subscript/Superscript missing or errors in case of Maths, Chemistry, Physics etc.
        - Incomplete question, options missing - Complete the question
        - Remove unnecessary words like Exam Name, Website Name, Page No., Question No., Exercise No., Points, Grade, Marks etc posted in question.
        - Question not making any sense can be marked as can not be fixed as status.
        - Fix Numbers, equation etc in latex, or math format missing.
        - Only mark question incomplete if you are changing any content in the question, even slight change in the content.
        - Always respond in latex code format.
        
        
         DO's :-
        1. Generate questions Using the same language, context, data
        2. Generate questions changing of context is not acceptable
        3. Question not making any sense or spam should be marked 'Cannot be fixed" rather than creating a question out of it.
        4. Latex code should be written in editable plain text like 2/3,2*3,80 degrees (signs in superscript). They should be written in a way so that they can be copied and pased in excel cell directly without using paste value tool.
        5. You can't change data and ask of the question
        6. If some question mention "as in figure", mark it "cannot be fixed" rather than creating a question out of it
        
        
        Examples :-
        Content: Movie Recommendation systems are an example of: 1. Classification 2. Clustering 3. Reinforcement Learning 4. Regression Options: B. A. 2 Only C. 1 and 2 D. 1 and 3 E. 2 and 3 F. 1, 2 and 3 H. 1, 2, 3 and 4
        Output: 
        question -> Movie Recommendation systems are an example of: 
        Classification 
        Clustering
        Reinforcement Learning 
        Regression 
        options -> ["2 Only", "1 and 2", "1 and 3", "2 and 3", "1, 2 and 3", "1, 2, 3 and 4"]
        status -> Complete 
        subject -> Mathematics 
        question_type -> MCQ
        
        Content: the giver's dwelling has may morebooks thn Jonas's	
        Output: 
        question -> None
        options -> None
        status -> Spam
        subject -> NotSure
        question_type -> MCQ
        
        Content: Define Medicare. Gray, Ryan. The Premed Playbook Guide to the Medical School Interview: Be Prepared, Perform Well, Get Accepted (p. 71). Morgan James Publishing. Kindle Edition.	
        Output: 
        question -> None
        options -> None
        status -> Cannot_Be_Fixed
        subject -> NotSure
        question_type -> MCQ
        
        Content: A customer has $100 to spend on buying a gift. They could make their purchase either at Cabela's or at Bass Pro. What competitive relationship exists between the two retailiers?	
        Output: 
        question -> A customer has $100 to spend on buying a gift. They could make their purchase either at Cabela's or at Bass Pro. What competitive relationship exists between the two retailiers?
        options -> []
        status -> Complete
        subject -> business
        question_type -> ShortAnswer
        
        """

    DEFAULT_USER_PROMPT_TEMPLATE = """
        Content: {task_objective}
        
        -----
        Please use the above input as the content for the question correction.
        """

    OTHER_USER_PROMPT_TEMPLATE = """
     Please use the above input as the content for the content correct analysis.
        You need to analyze the content & provide the correct content & their respective fields such as status.

        If Status is not Complete, then also provide the reason.

        Below the some Examples.
        1.
            Content: This climate diagram depicts ________. a. a tropical biome b. a very dry environment c. a typical boreal forest biome d. a biome with plentiful moisture e. a biome whose plants experience freeze stress for several months of the year

            Output:
            question - This climate diagram depicts ________.
            options -
            (A) a tropical biome
            (B) a very dry environment
            (C) a typical boreal forest biome
            (D) a biome with plentiful moisture
            (E) a biome whose plants experience freeze stress for several months of the year.

            status -> InComplete

        2.
            Content: In "Highlander II: The Quickening", we learn that the mysterious Immortals are actually aliens originating from the planet Zeist, a world that is referenced throughout the remainder of the Highlander series, but never actually shown.
            Output:
            question - Cannot be Fixed.
            status -> Cannot be Fixed
            reason -> Not an educational question.
        """

    DEFAULT_PARSER_SCHEMA = Question.function_schema()

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

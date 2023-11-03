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
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict

from superpilot.examples.ed_tech.question_solver import QuestionSolverPrompt


class SolutionValidatorPrompt(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT = """
        Solve question based on conversation of user and assistant for given Question, also fix the inaccuracies in solution:
        Solve the question in 3-4 steps, brief about question, step by step solution(use latex) and explanation of each step.
        make sure to answer the question on given conversation. Follow the below instructions.

        Instructions:
        - Write a complete answer without loosing symbols, equations, options, tables etc.
        - Write answer and equations in correct latex format.
        - Remove unnecessary brackets, words like Exam Name, Website Name, Page No., Question No., Exercise No., Points, Grade, Marks etc posted in question.
        - Do not engage in user conversation or ask any question. focus on only solving the question.
        - Please restrict the steps to less than 4 steps.
        - Do not include user and assistant conversation in the answer at all.
        - Please do not mention here is the formatted solution or here is the formatted answer, format answer as teacher answer a question.
        - Don't respond in json format, only text format is allowed as described below

        Step1:
            Brief
            Latex
            Explanation
        Step2:
            Brief
            Latex
            Explanation

        Final solution:

        Example:
        Step 1:
        The objective of this question is to evaluate the relationship between the concentration of a weak acid, its dissociation constant (Ka), and the resulting pH of the solution.
        Explanation:
        pH, which stands for "potential of hydrogen," is a measure of the acidity or alkalinity of a solution. It quantifies the concentration of hydrogen ions (H+) in a solution. The pH scale is a logarithmic scale that typically ranges from 0 to 14, with 7 being considered neutral:

        Step 2:
        To determine the pH of a solution of C6H5COOH (benzoic acid), we can use the formula for calculating the pH of a weak acid solution:
        pH = pKa + log([A-]/[HA])
        Where:
        - pKa is the negative logarithm (base 10) of the acid dissociation constant (Ka) of the acid.
        - [HA] is the concentration of the undissociated acid (C6H5COOH).
        It is given that the Ka (acid dissociation constant) of C6H5COOH is 6.5 x 10 -5. Therefore, we can find the pKa as follows:
        pKa = -log(6.5 x 10 -5)
        = 4.187
        Now, plug in the values into the pH equation and calculate the pH
        pH = 4.187 + log([C6H5COO -]/(C6H5COOH])
        The concentration of C6H5COOH as 9.461 M. Since C6H5COOH is a weak acid, it dissociates very little, so [A -] will be negligible compared to [HA].
        pH ≈ 4.187 + log(0)
        The closest option to a pH of 7 from the provided choices is 9.48.
        Explanation:
        The logarithm of zero is undefined, it means that in this solution, there is virtually no dissociation of C6H5COOH, and the concentration of H+ ions is very low. Consequently, the solution will be close to neutral, and the pH will be close to 7.

        Final answer:
        The pH of a. 9. 461 M C6H5COOH   M solution if the Ka of C6H5COOH is 6.5 x 10° will be 9.48
        So, option (b) is correct.

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
    ) -> "QuestionSolverPrompt":
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

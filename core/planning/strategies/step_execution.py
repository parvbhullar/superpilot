from typing import List

from superpilot.core.configuration import SystemConfiguration, UserConfigurable
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads, to_numbered_list
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
)
from superpilot.core.planning.schema import Task


class StepExecutionConfiguration(SystemConfiguration):
    model_classification: LanguageModelClassification = UserConfigurable()
    system_prompt_template: str = UserConfigurable()
    user_prompt_template: str = UserConfigurable()
    system_info: List[str] = UserConfigurable()
    additional_ability_arguments: dict = UserConfigurable()


class StepExecution(PromptStrategy):
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = "System Info:\n{system_info}"

    DEFAULT_SYSTEM_INFO = [
        "The OS you are running on is: {os_info}",
        "The current time and date is {current_time}",
    ]

    DEFAULT_USER_PROMPT_TEMPLATE = (
        "Your current task is is {task_objective}.\n"
        "Here is the actions you have taken and their results:\n"
        "{action_history}\n\n"
        "Below the next function will call as per the below schema:\n"
        "{ability_schema}\n\n"
        "You need to figureout the parameters for this function.\n"
        "Please provide the parameters appropiate for this function\n"
        "Your Answer should be in the following format:\n"
        "{output_schema}\n\n"
        "Example: \n"
        "{output_example}\n"
    )
    DEFAULT_ADDITIONAL_ABILITY_ARGUMENTS = {
        "function_call": {
            "type": "string",
            "description": "only name of the function to be called, just name",
        },
        "arguments": {
            "type": "object",
            "description": "parameter that needs to be passed to the function as per the function provided",
        },
    }

    default_configuration = StepExecutionConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt_template=DEFAULT_SYSTEM_PROMPT_TEMPLATE,
        system_info=DEFAULT_SYSTEM_INFO,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        additional_ability_arguments=DEFAULT_ADDITIONAL_ABILITY_ARGUMENTS,
    )

    def __init__(
        self,
        model_classification: LanguageModelClassification,
        system_prompt_template: str,
        system_info: List[str],
        user_prompt_template: str,
        additional_ability_arguments: dict,
    ):
        self._model_classification = model_classification
        self._system_prompt_template = system_prompt_template
        self._system_info = system_info
        self._user_prompt_template = user_prompt_template
        self._additional_ability_arguments = additional_ability_arguments

    @property
    def model_classification(self) -> LanguageModelClassification:
        return self._model_classification

    def build_prompt(
        self,
        task: Task,
        os_info: str,
        **kwargs,
    ) -> LanguageModelPrompt:
        ability_schema = kwargs.get(
            "ability_schema", [{"name": "No ability schema available."}]
        )
        ability_schema = ability_schema[0]
        template_kwargs = {
            "os_info": os_info,
            **kwargs,
        }

        template_kwargs["task_objective"] = task.objective
        template_kwargs["system_info"] = to_numbered_list(
            self._system_info,
            **template_kwargs,
        )
        template_kwargs["action_history"] = kwargs.get(
            "context", "You have not taken any actions yet."
        )
        template_kwargs["ability_schema"] = ability_schema
        template_kwargs["output_schema"] = self._additional_ability_arguments
        template_kwargs["output_example"] = {
            "function_call": "my_function",
            "arguments": {
                "param1": "value1",
                "param2": "value2",
            },
        }
        system_prompt = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_template.format(**template_kwargs),
        )
        user_prompt = LanguageModelMessage(
            role=MessageRole.USER,
            content=self._user_prompt_template.format(**template_kwargs),
        )
        functions = [LanguageModelFunction(json_schema=ability_schema)]

        return LanguageModelPrompt(
            messages=[system_prompt, user_prompt],
            functions=functions,
            # TODO:
            tokens_used=0,
        )

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
        parsed_response = json_loads(response_content["content"])
        parsed_response = {
            "next_ability": parsed_response.get("function_call"),
            "ability_arguments": parsed_response.get("arguments", {}),
        }
        return parsed_response

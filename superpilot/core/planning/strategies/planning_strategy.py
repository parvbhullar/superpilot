from abc import ABC

from superpilot.core.planning.strategies.simple import SimplePrompt

from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt, TaskStatus, TaskType, Task, TaskSchema, ObjectivePlan, ClarifyingQuestion,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    SchemaModel, OpenAIModelName, LanguageModelMessage, MessageRole, LanguageModelFunction,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict, Optional, List
import enum
from pydantic import Field


class PlanningStrategy(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = "System Info:\n{system_info}"

    DEFAULT_SYSTEM_INFO = [
        "The OS you are running on is: {os_info}",
        "It takes money to let you run. Your API budget is ${api_budget:.3f}",
        "The current time and date is {current_time}",
    ]

    DEFAULT_SYSTEM_PROMPT = """
    Review and comprehend the conversation to grasp the context and specifics of the task.
    Focus on the "{task_objective}" aspect of the larger task.
    Identify and list the relevant sub-tasks for the "{task_objective}" component.
    Reference the available functions: {functions}.
    Analyze how these functions can be applied to each sub-task.
    self reflect on your thoughts and reasoning for choosing the functions and then give final result.
    Ensure understanding aligns with the conversation details: {context}.
    """

    DEFAULT_USER_PROMPT_TEMPLATE = (
        ""
        # "Current user  is {task_objective}.\n"
        # "You have taken {cycle_count} actions on this task already. "
        # "Here is the actions you have taken and their results:\n"
        # "{action_history}\n\n"
    )

    DEFAULT_PARSER_SCHEMA = ObjectivePlan.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.planning.strategies.planning_strategy.PlanningStrategy",
        ),
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

    def build_prompt(self, **kwargs) -> LanguageModelPrompt:
        # print("kwargs",  v)
        model_name = kwargs.pop("model_name", OpenAIModelName.GPT3)
        template_kwargs = self.get_template_kwargs(kwargs)

        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message.format(**template_kwargs),
        )

        # self._parser_schema = ObjectivePlan.function_schema()

        # pilots = template_kwargs.pop("pilots", [])
        # 
        # pilot_enum = enum.Enum("Pilot", {value.get('name'): value.get('name') for value in pilots})

        # class PilotTaskSchema(TaskSchema):
        #     function_name: pilot_enum = Field(..., description="Name of the pilot/function most suited for this task")
        # 
        # class PilotObservation(ObjectivePlan):
        #     tasks: List[PilotTaskSchema] = Field(
        #         ..., description="List of tasks to be accomplished by the each pilot"
        #     )
        # 
        # self._parser_schema = PilotObservation.function_schema()

        # if model_name == OpenAIModelName.GPT4_VISION and "images" in template_kwargs:
        #     user_message = LanguageModelMessage(
        #         role=MessageRole.USER,
        #     )
        #     # print("VISION prompt", user_message)
        #     user_message = self._generate_content_list(user_message, template_kwargs)
        # else:
        #     user_message = LanguageModelMessage(
        #         role=MessageRole.USER,
        #         content=self._user_prompt_template.format(**template_kwargs)
        #     )

        functions = template_kwargs.pop("functions", [])

        function_enum = enum.Enum("Function", {value.get('name'): value.get('name') for value in functions})

        class PilotTaskSchema(TaskSchema):
            function_name: function_enum = Field(..., description="Name of the function most suited for this task")

        class PilotObjective(ObjectivePlan):
            tasks: List[PilotTaskSchema] = Field(
                ..., description="List of tasks to be accomplished"
            )

        function = {
            "name": "execute_functions",
            "description": "versatile function wrapper designed to execute multiple functions based on a structured "
                           "object passed as its argument. This function simplifies the process of calling multiple "
                           "functions with varying parameters by organizing the function calls and their respective "
                           "parameters in a single, unified structure.",
            "parameters": {
                "type": "object",
                "properties": {},
                # "required": ["ClarifyingQuestion", "PilotObservation"]
            }
        }

        for schema in [ClarifyingQuestion, PilotObjective]:
            function["parameters"]["properties"].update(
                schema.function_schema(arguments_format=True)
            )

        function = LanguageModelFunction(json_schema=function)
        functions = [function]
        # if self._parser_schema is not None:
        #     parser_function = LanguageModelFunction(
        #         json_schema=self._parser_schema,
        #     )
        #     functions.append(parser_function)

        prompt = LanguageModelPrompt(
            messages=[system_message],
            functions=functions,
            function_call=function,
            # TODO
            tokens_used=0,
        )
        return prompt

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
        # if "function_call" in response_content:
        #     parsed_response = json_loads(response_content["function_call"]["arguments"])
        # else:
        #     parsed_response = response_content
        # # print(response_content)
        # # parsed_response = json_loads(response_content["content"])
        # # parsed_response = self._parser_schema.from_response(response_content)
        # return parsed_response

        args = json_loads(response_content["function_call"]["arguments"])
        if args.get("ClarifyingQuestion"):
            parsed_response = args["ClarifyingQuestion"]
        else:
            parsed_response = args[list(args.keys())[0]] if args else {}
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response
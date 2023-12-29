from abc import ABC

from superpilot.core.planning.strategies.simple import SimplePrompt

from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt, TaskStatus, TaskType, Task, TaskSchema, ClarifyingQuestion,
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


class Observation(SchemaModel):
    """
    Planning of the objective, whether it is complete or not.
    If not complete, then the pilot name, motivation, self_criticism and reasoning for choosing the pilot.
    """
    current_status: TaskStatus = Field(..., description="Status of the objective asked by the user ")

    tasks: List[TaskSchema] = Field(
        ..., description="List of tasks to be accomplished by the each pilot"
    )

    def get_tasks(self) -> List[Task]:
        lst = []
        for task in self.tasks:
            lst.append(task.get_task())
        return lst


class ObserverPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = "System Info:\n{system_info}"

    DEFAULT_SYSTEM_INFO = [
        "The OS you are running on is: {os_info}",
        "It takes money to let you run. Your API budget is ${api_budget:.3f}",
        "The current time and date is {current_time}",
    ]

    DEFAULT_SYSTEM_PROMPT = """
    You are a expert assistant function calling capabilities.
    You always call the most appropriate function to accomplish the task.
    Understand the provided conversation thoroughly to understand the context and requirements of the tasks.
    Call the single most appropriate function considering the specific details and nuances of the current scenario.
    If anything is unclear, do not make assumptions and call ClarifyingQuestion function to gain a better understanding.

    Task:
    Assign each function from given functions a unique task based on the information gleaned from the
    conversation, ensuring no overlap in responsibilities.

    Functions:
    {pilots}


    Conversation:\n
    {context}
    """

    DEFAULT_USER_PROMPT_TEMPLATE = (
       ""
    )

    DEFAULT_PARSER_SCHEMA = Observation.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.ObserverPrompt",
        )
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

    def get_template_kwargs(self, kwargs):
        template_kwargs = super().get_template_kwargs(kwargs)
        template_kwargs["context"] = kwargs.get("context", "")
        return template_kwargs

    def build_prompt(self, **kwargs) -> LanguageModelPrompt:
        # print("kwargs",  v)
        model_name = kwargs.pop("model_name", OpenAIModelName.GPT3)
        template_kwargs = self.get_template_kwargs(kwargs)

        system_message = LanguageModelMessage(
            role=MessageRole.SYSTEM,
            content=self._system_prompt_message.format(**template_kwargs),
        )

        pilots = template_kwargs.pop("pilots", [])

        pilot_enum = enum.Enum("Pilot", {value.get('name'): value.get('name') for value in pilots})

        class PilotTaskSchema(TaskSchema):
            function_name: pilot_enum = Field(..., description="Name of the pilot/function most suited for this task")

        class PilotObservation(Observation):
            tasks: List[PilotTaskSchema] = Field(
                ..., description="List of tasks to be accomplished by the each pilot"
            )

        self._parser_schema = PilotObservation.function_schema()

        if model_name == OpenAIModelName.GPT4_VISION and "images" in template_kwargs:
            user_message = LanguageModelMessage(
                role=MessageRole.USER,
            )
            # print("VISION prompt", user_message)
            user_message = self._generate_content_list(user_message, template_kwargs)
        else:
            user_message = LanguageModelMessage(
                role=MessageRole.USER,
                content=self._user_prompt_template.format(**template_kwargs)
            )
            
        function = {
            "name": "Wrapper Function",
            "description": "function to call the most appropriate function",
            "parameters": {
                "properties": {
                    # TODO: add functon as properties
                }
            }
        }

        functions = []
        if self._parser_schema is not None:
            parser_function = LanguageModelFunction(
                json_schema=self._parser_schema,
            )
            functions.append(parser_function)

        functions.append(LanguageModelFunction(json_schema=ClarifyingQuestion.function_schema()))

        prompt = LanguageModelPrompt(
            messages=[system_message],
            functions=functions,
            function_call=LanguageModelFunction(json_schema={"functions": ["PilotObservation", "ClarifyingQuestion"]}),
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
        parsed_response = json_loads(response_content["function_call"]["arguments"])
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response

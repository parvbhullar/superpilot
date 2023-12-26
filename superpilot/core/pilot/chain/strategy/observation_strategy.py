from abc import ABC

from superpilot.core.planning.strategies.simple import SimplePrompt

from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt, TaskStatus, TaskType, Task, TaskSchema,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    SchemaModel, OpenAIModelName,
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

    DEFAULT_SYSTEM_PROMPT = """You are a skilled task coordinator. Analyze the given conversation and allocate tasks 
    among the pilots, ensuring each pilot is assigned one distinct task. Your role involves invoking the most 
    suitable function based on the current scenario. Refrain from making assumptions and seek clarifications if the 
    task's objective is unclear.

    Pilot Roster:
    {pilots}

    Examine the following dialogue between the assistant and the user, along with corresponding events. Then, proceed accordingly:\n
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

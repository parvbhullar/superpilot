from abc import ABC

from superpilot.core.planning.strategies.simple import SimplePrompt

from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt, TaskStatus, TaskType, Task, TaskSchema, ObjectivePlan,
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


class PlanningStrategy(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = "System Info:\n{system_info}"

    DEFAULT_SYSTEM_INFO = [
        "The OS you are running on is: {os_info}",
        "It takes money to let you run. Your API budget is ${api_budget:.3f}",
        "The current time and date is {current_time}",
    ]

    DEFAULT_SYSTEM_PROMPT = """
        You are a world class query/task planning algorithm capable of thinking step by step and breaking apart tasks 
        into its corrected version of tasks. Do not answer the questions, simply provide correct dependency graph 
        with good specific questions to ask based the provided conversation. Map tasks with most suited function in 
        correct execution order.
        
        Available Functions:
        {functions}
        
        Example:
        task: multiply 2 and 3 and then sum with 6
        response:
          'current_status': 'backlog',
          'motivation': "The task requires both arithmetic operations and plotting, which can be accomplished by the 'calculator' pilot",
          'self_criticism': "The task involves plotting a graph which is not a specific function of the 'calculator' pilot.",
          'reasoning': "Despite the limitation, the 'calculator' pilot can still handle the arithmetic operations which makes up the majority of the task",
          'tasks': [
              'objective': 'multiply 2 and 3',
              'type': 'code',
              'priority': 1,
              'ready_criteria': [
                'Inputs are valid'
              ],
              'acceptance_criteria': [
                'Return correct computation result'
              ],
              'status': 'backlog',
              'function_name': 'multiply_ability'
            ,
              'objective': 'Sum result with 6',
              'type': 'code',
              'priority': 5,
              'ready_criteria': [
                'Multiplication result is available'
              ],
              'acceptance_criteria': [
                'Return correct sum'
              ],
              'status': 'backlog',
              'function_name': ''
          ]
        
        """

    DEFAULT_USER_PROMPT_TEMPLATE = (
        "Current user  is {task_objective}.\n"
        "You have taken {cycle_count} actions on this task already. "
        "Here is the actions you have taken and their results:\n"
        "{action_history}\n\n"
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
        if "function_call" in response_content:
            parsed_response = json_loads(response_content["function_call"]["arguments"])
        else:
            parsed_response = response_content
        # print(response_content)
        # parsed_response = json_loads(response_content["content"])
        # parsed_response = self._parser_schema.from_response(response_content)
        return parsed_response

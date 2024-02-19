from abc import ABC

from superpilot.core.planning.strategies.simple import SimplePrompt

from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt, TaskStatus, TaskType, Task,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    SchemaModel, OpenAIModelName,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict, Optional, List
import enum
from pydantic import Field


class TaskSchema(SchemaModel):
    """
    Class representing the data structure for task for pilot objective, whether it is complete or not.
    """
    objective: str = Field(..., description="An verbose description of the task.")
    type: TaskType = Field(
        default=TaskType.RESEARCH,
        description="A categorization for the task from [research, write, edit, code, design, test, plan].")
    priority: int = Field(..., description="A number between 1 and 10 indicating the priority of the task "
                                           "relative to other generated tasks.")
    ready_criteria: List[str] = Field(..., description="A list of measurable and testable criteria that must "
                                                       "be met for the "
                                                       "task to be considered complete.")
    acceptance_criteria: List[str] = Field(..., description="A list of measurable and testable criteria that "
                                                            "must be met before the task can be started.")
    status: TaskStatus = Field(
        default=TaskStatus.BACKLOG,
        description="The current status of the task from [backlog, in_progress, complete, on_hold].")
    function_name: str = Field(..., description="Name of the pilot/function most suited for this task")
    motivation: str = Field(..., description="Your justification for choosing this pilot instead of a different one.")
    self_criticism: str = Field(..., description="Thoughtful self-criticism that explains why this pilot may not be "
                                                 "the best choice.")
    reasoning: str = Field(..., description="Your reasoning for choosing this pilot taking into account the "
                                            "`motivation` and weighing the `self_criticism`.")

    def get_task(self) -> Task:
        return Task.factory(self.objective, self.type, self.priority, self.ready_criteria, self.acceptance_criteria, status=self.status)


class Observation(SchemaModel):
    """
    Class representing the data structure for observation for pilot objective, whether it is complete or not.
    If not complete, then the pilot name, motivation, self_criticism and reasoning for choosing the pilot.
    """
    current_status: TaskStatus = Field(..., description="Status of the objective asked by the user ")

    tasks: List[TaskSchema] = Field(
        ..., description="List of tasks to be accomplished by the each pilot"
    )

    # def get_tasks(self) -> List[Task]:
    #     lst = []
    #     for task in self.tasks:
    #         lst.append(task.get_task())
    #     return lst


class ObserverPrompt(SimplePrompt, ABC):
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = "System Info:\n{system_info}"

    DEFAULT_SYSTEM_INFO = [
        "The OS you are running on is: {os_info}",
        "It takes money to let you run. Your API budget is ${api_budget:.3f}",
        "The current time and date is {current_time}",
    ]

    DEFAULT_SYSTEM_PROMPT = """
        you are an expert task observer. Read the provided conversation. 
        Then select the next pilot from pilots list to play. 
        Split task between pilots and each pilot should have a single task in sequence.
        
        Pilot List:
        {pilots}
        
        Example:
        task: multiply 2 and 3 and then sum with 6 and then subtract 2 and then divide by 2 and plot the graph
        response:
          'current_status': 'backlog',
          'tasks': [
              'objective': 'multiply 2 and 3 and then sum with 6 and then subtract 2 and then divide by 2',
              'type': 'code',
              'priority': 1,
              'ready_criteria': [
                'Inputs are valid'
              ],
              'acceptance_criteria': [
                'Return correct computation result'
              ],
              'status': 'backlog',
              'function_name': 'calculator'
            ,
              'objective': 'Plot the graph',
              'type': 'code',
              'priority': 5,
              'ready_criteria': [
                'Division result is available'
              ],
              'acceptance_criteria': [
                'Return correct plot'
              ],
              'status': 'backlog',
              'function_name': ''
          ]
        
        """

    DEFAULT_USER_PROMPT_TEMPLATE = (
        "Your current task is {task_objective}.\n"
        "You have taken {cycle_count} actions on this task already. "
        "Here is the actions you have taken and their results:\n"
        "{action_history}\n\n"
    )

    DEFAULT_PARSER_SCHEMA = Observation.function_schema()

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

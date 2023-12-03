from abc import ABC

from superpilot.core.planning.strategies.simple import SimplePrompt

from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt, TaskStatus, TaskType,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    SchemaModel, OpenAIModelName,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from typing import Dict, Optional, List
import enum
from pydantic import Field


class ObservationStatus(str, enum.Enum):
    """The LanguageModelClassification is a functional description of the model.

    This is used to determine what kind of model to use for a given prompt.
    Sometimes we prefer a faster or cheaper model to accomplish a task when
    possible.

    """
    NOT_STARTED: str = "not_started"
    INCOMPLETE: str = "incomplete"
    COMPLETE: str = "complete"
    ON_HOLD: str = "on_hold"


class Task(SchemaModel):
    """
    Class representing the data structure for task for pilot objective, whether it is complete or not.
    """
    objective: str = Field(..., description="An imperative verb phrase that succinctly describes the task.")
    type: TaskType = Field(
        default=TaskType.RESEARCH,
        description="A categorization for the task.")
    priority: int = Field(..., description="A number between 1 and 10 indicating the priority of the task "
                                           "relative to other generated tasks.")
    ready_criteria: List[str] = Field(..., description="A list of measurable and testable criteria that must "
                                                       "be met for the "
                                                       "task to be considered complete.")
    acceptance_criteria: List[str] = Field(..., description="A list of measurable and testable criteria that "
                                                            "must be met before the task can be started.")
    status: TaskStatus = Field(
        default=TaskStatus.BACKLOG,
        description = "The current status of the task.")
    pilot_name: str = Field(..., description="Name of the pilot most suited for this task")


class Observation(SchemaModel):
    """
    Class representing the data structure for observation for pilot objective, whether it is complete or not.
    If not complete, then the pilot name, motivation, self_criticism and reasoning for choosing the pilot.
    """
    goal_status: ObservationStatus = Field(..., description="Status of the objective asked by the user")
    motivation: str = Field(..., description="Your justification for choosing this pilot instead of a different one.")
    self_criticism: str = Field(..., description="Thoughtful self-criticism that explains why this pilot may not be "
                                                 "the best choice.")
    reasoning: str = Field(..., description="Your reasoning for choosing this pilot taking into account the "
                                            "`motivation` and weighing the `self_criticism`.")

    tasks: List[Task] = Field(
        ..., description="List of tasks to be accomplished by the each pilot"
    )


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
          'goal_status': 'not_started',
          'motivation': "The task requires both arithmetic operations and plotting, which can be accomplished by the 'calculator' pilot",
          'self_criticism': "The task involves plotting a graph which is not a specific function of the 'calculator' pilot.",
          'reasoning': "Despite the limitation, the 'calculator' pilot can still handle the arithmetic operations which makes up the majority of the task",
          'tasks': [
              'objective': 'multiply 2 and 3 and then sum with 6 and then subtract 2 and then divide by 2',
              'type': 'Arithmetic',
              'priority': 1,
              'ready_criteria': [
                'Inputs are valid'
              ],
              'acceptance_criteria': [
                'Return correct computation result'
              ],
              'status': 'not_started',
              'pilot_name': 'calculator'
            ,
              'objective': 'Plot the graph',
              'type': 'Plot',
              'priority': 5,
              'ready_criteria': [
                'Division result is available'
              ],
              'acceptance_criteria': [
                'Return correct plot'
              ],
              'status': 'not_started',
              'pilot_name': ''
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

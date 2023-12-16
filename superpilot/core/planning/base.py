import abc
import typing

from superpilot.core.configuration import SystemConfiguration, UserConfigurable
from superpilot.core.context.schema import Context
# Cyclic import
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelMessage,
    LanguageModelPrompt, LanguageModelResponse, ObjectivePlan, Task,
)
from superpilot.core.resource.model_providers import SchemaModel


class Planner(abc.ABC):
    """Manages the pilot's planning and goal-setting by constructing language model prompts."""

    # @staticmethod
    # @abc.abstractmethod
    # async def decide_name_and_goals(
    #     user_objective: str,
    # ) -> LanguageModelResponse:
    #     """Decide the name and goals of an Agent from a user-defined objective.
    #
    #     Args:
    #         user_objective: The user-defined objective for the pilot.
    #
    #     Returns:
    #         The pilot name and goals as a response from the language model.
    #
    #     """
    #     ...

    @abc.abstractmethod
    async def plan(self, user_objective: str, context: Context) -> ObjectivePlan:
        """Create a plan of tasks to accomplish the user objective.

        Args:
            user_objective: The user objective for the pilot.
            context: A context object containing information about the pilot's
                       progress, result, memories, and feedback.


        Returns:
            A plan of tasks to accomplish the user objective.
        """
        ...

    @abc.abstractmethod
    async def next(self, task: Task, context: Context) -> LanguageModelResponse:
        """Based of the current task, decide the next executable function, pilot or ability.

        Args:
            task: The current task.
            context: A context object containing information about previous execution and results.

        Returns:
            The next function, pilot or ability to execute.
        """
        ...

    @abc.abstractmethod
    def reflect(
        self,
        task: Task,
        context: Context,
    ) -> LanguageModelResponse:
        """Reflect on executed function, pilot or ability. Provide feedback to the user.

        Args:
            task: The current task.
            context: A context object containing information about the pilot's
                       reasoning, plan, thoughts, and criticism.

        Returns:
            Self-criticism about the pilot's plan.

        """
        ...


class PromptStrategy(abc.ABC):
    default_configuration: SystemConfiguration

    @property
    @abc.abstractmethod
    def model_classification(self) -> LanguageModelClassification:
        ...

    @abc.abstractmethod
    def build_prompt(self, *_, **kwargs) -> LanguageModelPrompt:
        ...

    @abc.abstractmethod
    def parse_response_content(self, response_content: dict) -> dict:
        ...

import abc
import typing

from superpilot.core.configuration import SystemConfiguration, UserConfigurable
# Cyclic import
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelMessage,
    LanguageModelPrompt,
)

# class Planner(abc.ABC):
#     """Manages the pilot's planning and goal-setting by constructing language model prompts."""
#
#     @staticmethod
#     @abc.abstractmethod
#     async def decide_name_and_goals(
#         user_objective: str,
#     ) -> LanguageModelResponse:
#         """Decide the name and goals of an Agent from a user-defined objective.
#
#         Args:
#             user_objective: The user-defined objective for the pilot.
#
#         Returns:
#             The pilot name and goals as a response from the language model.
#
#         """
#         ...
#
#     @abc.abstractmethod
#     async def plan(self, context: PlanningContext) -> LanguageModelResponse:
#         """Plan the next ability for the Agent.
#
#         Args:
#             context: A context object containing information about the pilot's
#                        progress, result, memories, and feedback.
#
#
#         Returns:
#             The next ability the pilot should take along with thoughts and reasoning.
#
#         """
#         ...
#
#     @abc.abstractmethod
#     def reflect(
#         self,
#         context: ReflectionContext,
#     ) -> LanguageModelResponse:
#         """Reflect on a planned ability and provide self-criticism.
#
#
#         Args:
#             context: A context object containing information about the pilot's
#                        reasoning, plan, thoughts, and criticism.
#
#         Returns:
#             Self-criticism about the pilot's plan.
#
#         """
#         ...


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

import abc
from typing import ClassVar

import inflection

from superpilot.core.context.schema import Context
from superpilot.core.pilot.chain.strategy.observation_strategy import Observation
from superpilot.core.pilot.task.settings import TaskPilotConfiguration
from superpilot.core.pilot.base import Pilot


class TaskPilot(Pilot, abc.ABC):
    """A class representing a pilot step."""

    default_configuration: ClassVar[TaskPilotConfiguration]

    @classmethod
    def name(cls) -> str:
        """The name of the step."""
        return inflection.underscore(cls.__name__)

    @abc.abstractmethod
    async def execute(self, *args, **kwargs) -> Context:
        ...

    # @abc.abstractmethod
    # async def observe(self, *args, **kwargs) -> Observation:
    #     ...

    @abc.abstractmethod
    def __repr__(self):
        ...

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

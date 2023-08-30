import abc
from typing import ClassVar

import inflection

from superpilot.core.context.schema import Context
from superpilot.core.flow.settings import TaskPilotConfiguration


class TaskPilot(abc.ABC):
    """A class representing a pilot step."""

    default_configuration: ClassVar[TaskPilotConfiguration]

    @classmethod
    def name(cls) -> str:
        """The name of the step."""
        return inflection.underscore(cls.__name__)

    @abc.abstractmethod
    async def execute(self, *args, **kwargs) -> Context:
        ...

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

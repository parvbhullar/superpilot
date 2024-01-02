import abc
import logging
from pathlib import Path
import inflection

from superpilot.core.context.schema import Message
from superpilot.core.planning.schema import TaskPlan, Task, LanguageModelResponse


class Run(abc.ABC):

    @abc.abstractmethod
    async def run(self, message: Message, *args, **kwargs) -> Message:
        """Execute the based on given user message."""
        ...

    @abc.abstractmethod
    async def execute(self, task: Task, *args, **kwargs) -> LanguageModelResponse:
        """Execute the based on given user message."""
        ...

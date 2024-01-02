import abc
import logging
from pathlib import Path
import inflection

from superpilot.core.context.schema import Message
from superpilot.core.pilot.execution.base import Run
from superpilot.core.planning.schema import TaskPlan


class SimpleExecution(Run):
    def __init__(self, *args, **kwargs):
        ...

    async def run(self, message: Message, *args, **kwargs) -> Message:
        pass

    async def execute(self, message: Message, *args, **kwargs) -> Message:
        """Execute the based on given user message."""

        # check for thread/context
        # See if any task plan needs to be created or updated
        # See if any task needs to be executed





import abc
import logging
from pathlib import Path
import inflection

from superpilot.core.callback.base import BaseCallback


class SimpleCallbackHandler(BaseCallback):

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__), thread_id: str = None, **kwargs):
        self._logger = logger
        self._thread_id = thread_id

    async def on_chain_start(self, *args, **kwargs):
        print("SimpleCallbackHandler.on_chain_start")

    async def on_pilot_execute(self, *args, **kwargs):
        print("SimpleCallbackHandler.on_pilot_execute")

    async def on_ability_perform(self, *args, **kwargs):
        print("SimpleCallbackHandler.on_ability_perform")

    async def on_info(self, *args, **kwargs):
        print("Info: ", args, kwargs)

    async def on_execution(self, *args, **kwargs):
        print("Execution: ", args, kwargs)

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)


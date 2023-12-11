import abc
import logging
from pathlib import Path
from typing import List

import asyncio
import inflection

from superpilot.core.callback.base import BaseCallback
from superpilot.core.callback.handler.base import BaseCallbackHandler
from superpilot.core.callback.manager.base import BaseCallbackManager


class SimpleCallbackManager(BaseCallbackManager):

    @abc.abstractmethod
    def __init__(self, callbacks: List[BaseCallbackHandler], logger: logging.Logger):
        self._callbacks = callbacks
        self._logger = logger

    @abc.abstractmethod
    async def on_chain_start(self, *args, **kwargs):
        handlers = [
            self.perform_ability(self._current_task, [ability.dump()], **kwargs)
            for ability in self._callbacks
        ]
        res_list = await asyncio.gather(*handlers)
        return res_list

    @abc.abstractmethod
    async def on_pilot_execute(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def on_ability_perform(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def on_clarifying_question(self, *args, **kwargs):
        ...

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)


import abc
import logging
from pathlib import Path
from typing import List

import inflection

from superpilot.core.callback.base import BaseCallback
from superpilot.core.callback.handler.base import BaseCallbackHandler


class BaseCallbackManager(BaseCallback):

    @abc.abstractmethod
    def __init__(self, callbacks: List[BaseCallbackHandler], logger: logging.Logger):
        self._callbacks = callbacks
        self._logger = logger

    @abc.abstractmethod
    async def on_clarifying_question(self, *args, **kwargs):
        ...

    async def on_user_interaction(self, *args, **kwargs):
        pass

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)


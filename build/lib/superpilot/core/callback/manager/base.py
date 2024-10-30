import abc
import logging
from pathlib import Path
from typing import List, Tuple

import inflection

from superpilot.core.callback.base import BaseCallback
from superpilot.core.callback.handler.base import BaseCallbackHandler
from superpilot.core.context.schema import Message, Context
from superpilot.core.planning import Task, LanguageModelResponse


class BaseCallbackManager(BaseCallback):

    @abc.abstractmethod
    def __init__(self, callbacks: List[BaseCallbackHandler], logger: logging.Logger, thread_id: str = None, **kwargs):
        self._callbacks = callbacks
        self._logger = logger
        self._thread_id = thread_id

    @abc.abstractmethod
    async def on_clarifying_question(
        self,
        question_message: Message,
        current_task: Task,
        response: LanguageModelResponse,
        context: Context,
        *args,
        **kwargs
    ) -> Tuple[Message, bool]:
        ...

    async def on_user_interaction(self, *args, **kwargs):
        pass

    async def on_observation(self, observation, *args, **kwargs):
        pass

    async def on_chain_complete(self, *args, **kwargs):
        pass

    async def on_execution_complete(self, *args, **kwargs):
        pass

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

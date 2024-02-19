import logging
from typing import List, Tuple

import inflection

from superpilot.core.callback.handler.base import BaseCallbackHandler
from superpilot.core.callback.manager.base import BaseCallbackManager
from superpilot.core.callback.manager.callback_runner import handle_event


class STDInOutCallbackManager(BaseCallbackManager):

    def __init__(self, callbacks: List[BaseCallbackHandler] = None, logger: logging.Logger = logging.getLogger(__name__)):
        self._callbacks = callbacks
        self._logger = logger

    async def on_chain_start(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_chain_start", *args, **kwargs)

    async def on_pilot_execute(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_pilot_execute", *args, **kwargs)

    async def on_ability_perform(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_ability_perform", *args, **kwargs)

    async def on_info(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_info", *args, **kwargs)

    async def on_clarifying_question(self, question, current_task, response, current_context, thread_id, *args, **kwargs) -> Tuple[str, bool]:
        print("Question ", question)
        try:
            user_input = input("Enter your response: ")
            return user_input, False
        except KeyboardInterrupt:
            return "", True

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

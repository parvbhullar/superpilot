import logging
from typing import List, Tuple

import inflection

from superpilot.core.callback.handler.base import BaseCallbackHandler
from superpilot.core.callback.manager.base import BaseCallbackManager
from superpilot.core.callback.manager.callback_runner import handle_event
from superpilot.core.context.schema import Message, Context
from superpilot.core.planning import Task, LanguageModelResponse


class STDInOutCallbackManager(BaseCallbackManager):

    def __init__(self, callbacks: List[BaseCallbackHandler] = None, logger: logging.Logger = logging.getLogger(__name__), thread_id: str = None, **kwargs):
        self._callbacks = callbacks
        self._logger = logger
        self._thread_id = thread_id

    async def on_chain_start(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_chain_start", *args, **kwargs)

    async def on_pilot_execute(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_pilot_execute", *args, **kwargs)

    async def on_ability_perform(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_ability_perform", *args, **kwargs)

    async def on_info(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_info", *args, **kwargs)

    async def on_execution(self, *args, **kwargs):
        await handle_event(self._callbacks, "on_execution", *args, **kwargs)

    async def on_clarifying_question(
        self,
        question_message: Message,
        current_task: Task,
        response: LanguageModelResponse,
        context: Context,
        *args,
        **kwargs
    ) -> Tuple[Message, bool]:
        print("Question ", question_message.message)
        try:
            user_input = input("Enter your response: ")
            user_message = Message.add_user_message(message=user_input)
            return user_message, False
        except KeyboardInterrupt:
            return None, True

    async def model_req_res_callback(
            self,
            model_prompt,
            functions,
            response,
            parsed_response,
            response_args,
            *args, **kwargs
    ):
        thread_id = self._thread_id
        data = {
            "conversationId": thread_id,
            "model_prompt": [message.dict() for message in model_prompt],
            "functions": [function.json_schema for function in functions],
            "response": response.dict(),
            "parsed_response": parsed_response,
            "response_args": response_args,
        }
        print(data)

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

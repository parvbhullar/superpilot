import logging
from abc import abstractmethod


class CallbackHandler:
    def __init__(self, callback):
        self.callback = callback

    @abstractmethod
    async def transformer(self, task, context, **kwargs):
        pass

    @abstractmethod
    async def on_chain_start(self, task, context, **kwargs):
        pass

    @abstractmethod
    async def on_chain_finish(self, task, context, **kwargs):
        pass

    @abstractmethod
    async def on_observation(self, task, context, **kwargs):
        pass

    @abstractmethod
    async def on_ability_execution(self, task, context, **kwargs):
        pass

    @abstractmethod
    async def on_ability_response(self, task, context, **kwargs):
        pass


class DefaultCallbackHandler(CallbackHandler):
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        self._logger = logger

    async def transformer(self, task, context, **kwargs):
        return task, context

    async def on_chain_start(self, task, context, **kwargs):
        self._logger.info(f"Starting chain {task}")

    async def on_chain_finish(self, task, context, **kwargs):
        pass

    async def on_observation(self, task, context, **kwargs):
        pass

    async def on_ability_execution(self, task, context, **kwargs):
        pass

    async def on_ability_response(self, task, context, **kwargs):
        pass


class MessagingCallbackHandler(CallbackHandler):
    def __init__(self, web_socket, logger: logging.Logger = logging.getLogger(__name__)):
        self._logger = logger
        self._web_socket = web_socket

    async def on_handler_response(self, task, context, **kwargs):
        return task, context

    async def on_chain_start(self, task, context, **kwargs):
        self._logger.info(f"Starting chain {task}")
        self._web_socket.send(f"Starting chain {task}")

    async def on_chain_finish(self, task, context, **kwargs):
        pass

    async def on_observation(self, task, context, **kwargs):
        pass

    async def on_ability_execution(self, task, context, **kwargs):
        pass

    async def on_ability_response(self, task, context, **kwargs):
        pass


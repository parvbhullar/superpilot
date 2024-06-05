from abc import ABC, abstractmethod
import logging


class BaseChain(ABC):
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__), **kwargs):
        self.logger = logger
        self.handlers = []
        self.transformers = []

    def add_handler(self, handler, transformer=None):
        """
        Adds a handler and an optional transformer to the chain.
        """
        self.handlers.append(handler)
        self.transformers.append(transformer or None)

    def default_transformer(self, data, response, context):
        response = response.get("content", data)
        return response, context

    async def execute(self, data, context, **kwargs):
        self.total_cost = {}
        for handler, transformer in zip(self.handlers, self.transformers):
            try:
                # Check if the handler is a function or a class with an execute method
                if callable(handler):
                    response = await handler(data, context, **kwargs)
                else:
                    response = await handler.execute(data, context, **kwargs)
                if transformer:
                    data, context = transformer(
                        data=data, response=response, context=context
                    )
                else:
                    data = response
                self.update_cost(response)
            except Exception as e:
                import traceback

                self.logger.error(
                    f"Error in handler {handler.name()}: {e} {traceback.print_exc()}"
                )
                continue
        return data, context

    @abstractmethod
    async def execute_handler(self, handler, data, context, **kwargs):
        pass

    def remove_handler(self, handler_index):
        """
        Removes a handler from the chain.
        """
        self.handlers.pop(handler_index)
        self.transformers.pop(handler_index)

    def update_cost(cls, response):
        if hasattr(response, "total_cost"):
            total_cost = response.total_cost
            completion_tokens_used = response.completion_tokens_used
            prompt_tokens_used = response.prompt_tokens_used
            cls.total_cost["total_cost"] = (
                cls.total_cost.get("total_cost", 0) + total_cost
            )
            cls.total_cost["completion_tokens_used"] = (
                cls.total_cost.get("completion_tokens_used", 0) + completion_tokens_used
            )
            cls.total_cost["prompt_tokens_used"] = (
                cls.total_cost.get("prompt_tokens_used", 0) + prompt_tokens_used
            )

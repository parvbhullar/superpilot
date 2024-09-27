from .base import BaseChain, HandlerType


class SimpleChain(BaseChain):
    async def execute(self, data, context, **kwargs):
        for handler, transformer in zip(
            self.pilots[HandlerType.HANDLER], self.transformers[HandlerType.HANDLER]
        ):
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
            except Exception as e:
                import traceback

                self.logger.error(
                    f"Error in handler {handler.name()}: {e} {traceback.print_exc()}"
                )
                continue
        return data, context

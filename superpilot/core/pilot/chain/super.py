import logging
from superpilot.core.pilot.chain.base import BaseChain, HandlerType

from superpilot.core.ability import AbilityAction
from superpilot.core.context.schema import Context
from superpilot.core.pilot.chain.strategy.observation_strategy import Observation, ObservationStatus
from superpilot.core.planning import TaskStatus, Task, LanguageModelResponse


class SuperChain(BaseChain):
    def __init__(self,
                 logger: logging.Logger = logging.getLogger(__name__),
                 **kwargs):
        super().__init__(logger, **kwargs)
        self.logger = logger
        self._task_queue = []
        self._completed_tasks = []
        self._current_task = None
        self._next_step = None

    async def execute(self, task: str, context: Context, **kwargs):
        # TODO: Add a check to see if task needs to be created as multiple tasks
        # TODO: observe which pilot is suitable for the task and then execute it
        # TODO: Add a verify if the task is complete or not and if require run the task again based on given context

        while True:
            observation = await self.observe(task, context)
            if observation:
                if observation.task_status == ObservationStatus.COMPLETE:
                    return "The task is completed successfully", context  # TODO fix this
                else:
                    handler, transformer = self.current_handler(observation.pilot_name)
                    response, context = await self.execute_handler(task, context, handler, transformer, **kwargs)
                    print("response", response)
                    print("context", context)
                    # return task, context
            else:
                return "Either observation or observer is not defined, please set observer in the chain.", context

    async def execute_handler(self, task, context: Context, handler, transformer, **kwargs):
        response = None
        try:
            # Check if the handler is a function or a class with an execute method
            if callable(handler):
                response = await handler(task, context, **kwargs)
            else:
                response = await handler.execute(task, context, **kwargs)

            if isinstance(response, LanguageModelResponse):
                context.add(response.get_content())
            elif isinstance(response, Context):
                context.extend(response)
            elif isinstance(response, AbilityAction):
                pass
            if transformer:
                response, context = transformer(data=task, response=response, context=context)

        except Exception as e:
            import traceback
            self.logger.error(f"Error in handler {handler.name()}: {e} {traceback.print_exc()}")
        return response, context

    async def observe(self, task, context) -> Observation:
        observer = self.current_observer()
        if observer:
            try:
                response = await observer.execute(task, context, pilots=self.dump_pilots())
                # TODO : send the consumtion metrics to service
                print("response", response)
                return Observation(**response.get_content())
            except Exception as e:
                import traceback
                self.logger.error(f"Error in observer {observer.name()}: {e} {traceback.print_exc()}")
                return None
        return None
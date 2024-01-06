import logging
from superpilot.core.pilot.chain.base import BaseChain, HandlerType

from superpilot.core.ability import AbilityAction
from superpilot.core.context.schema import Context
from superpilot.core.pilot.chain.strategy.observation_strategy import Observation
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
        self._current_observation = None
        self._next_step = None

    async def execute(self, objective: str, context: Context, **kwargs):
        # Splitting the observation and execution phases
        observation = await self.observe(objective, context)
        if observation:
            self._current_observation = observation
            self._task_queue = observation.tasks
            kwargs['current_chain'] = self
            return await self.handle_task_based_on_observation(context, **kwargs)
        else:
            return "Either observation or observer is not defined, please set observer in the chain.", context

    async def handle_task_based_on_observation(self, context: Context, **kwargs):
        # Logic to choose the right function and its arguments based on the observation
        if self._current_observation.current_status != TaskStatus.DONE:
            response = None
            for task_in_hand in self._task_queue:
                self._current_task = task_in_hand
                if task_in_hand.status != TaskStatus.DONE:
                    handler, transformer = self.current_handler(task_in_hand.function_name)
                    if handler is None:
                        # TODO : Add a check to see if the task needs to be created as multiple tasks
                        # return f"Handler named '{task_in_hand.function_name}' is not defined", context
                        self.logger.error(f"Handler named '{task_in_hand.function_name}' is not defined")
                        continue
                    # TODO: there should be Pilot Task where we store the pilot Action?
                    response, context = await self.execute_handler(task_in_hand.objective, context, handler, transformer, **kwargs)
            if response:
                # TODO: this task is different from the one in superpilot
                self._current_task.status = TaskStatus.DONE
                self._completed_tasks.append(self._current_task)
                self._task_queue.remove(self._current_task)
                return response, context
            else:
                return "There was some issue", context
        else:
            return "Task is already completed", context

    async def execute_handler(self, task, context: Context, handler, transformer, **kwargs):
        response = None
        try:
            # Check if the handler is a function or a class with an execute method
            if callable(handler):
                response = await handler(task, context=context, **kwargs)
            else:
                response = await handler.execute(task, context=context, **kwargs)

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

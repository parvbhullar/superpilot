import logging
from superpilot.core.pilot.chain.base import BaseChain, HandlerType

from superpilot.core.ability import AbilityAction
from superpilot.core.context.schema import Context
from superpilot.core.pilot.chain.strategy.observation_strategy import Observation
from superpilot.core.planning import TaskStatus, Task, LanguageModelResponse
from superpilot.core.state.base import BaseState
from superpilot.core.state.mixins import DictStateMixin, PickleStateMixin


class SuperChain(BaseChain, DictStateMixin, PickleStateMixin):

    def __init__(
        self,
        logger: logging.Logger = logging.getLogger(__name__),
        state: BaseState = None,
        **kwargs
    ):
        super().__init__(logger, **kwargs)
        self.logger = logger
        self._interaction = False

        self._current_observation = None
        self._task_queue = []
        self._completed_tasks = []
        self._current_task = None
        self._task_index = 0
        self._response = None
        self._context = Context()
        self._pilot_state = {}

        # load the values from state
        self._state = state

    async def execute(self, objective: str, context: Context, **kwargs):
        # Splitting the observation and execution phases
        state = await self._state.load()
        await self._state.deserialize(self, state)
        kwargs['current_chain'] = self
        self._interaction = False
        if not self._current_observation:
            observation = await self.observe(objective, context)
            if not observation:
                return "Either observation or observer is not defined, please set observer in the chain.", context
            self._current_observation = observation
            self._task_queue = observation.tasks
            self._pilot_state = {}

        while self._task_index < len(self._task_queue):
            self._response, self._context = await self.execute_next(self._response, self._context, **kwargs)
            # TODO: interaction can be more  types, some may hault the execution and some may continue right after interaction immedatly (like..question and info)
            if self._interaction:
                break
        return self._response, self._context

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
                # self._task_queue.remove(self._current_task)
                return response, context
            else:
                return "There was some issue", context
        else:
            return "Task is already completed", context

    async def execute_next(self, response, context: Context, **kwargs):
        self._current_task = self._task_queue[self._task_index]
        if self._current_task.status != TaskStatus.DONE:
            handler, transformer = self.current_handler(self._current_task.function_name)
            if handler is None:
                # TODO : Add a check to see if the task needs to be created as multiple tasks
                # return f"Handler named '{task_in_hand.function_name}' is not defined", context
                # TODO: Remove posibilty of null handler, or handle the situation...(dont start execution without confirming the flow from anther plan observer) - (planner, plan observer internal talks)
                self.logger.error(f"Handler named '{self._current_task.function_name}' is not defined")
                self._task_index += 1
            else:
                # TODO: there should be Pilot Task where we store the pilot Action?
                await self._state.deserialize(handler, self._pilot_state)
                response, context = await self.execute_handler(self._current_task.objective, context, handler, transformer, **kwargs)
                # TODO: Make it interaction based?
                if self._pilot_state.get('_status', TaskStatus.DONE) == TaskStatus.DONE:
                    self._pilot_state = {}
                    self._current_task.status = TaskStatus.DONE
                    self._completed_tasks.append(self._current_task)
                    self._task_index += 1
                else:
                    self._current_task.status = TaskStatus.IN_PROGRESS
                    self._interaction = True
                    current_state = await self._state.serialize(self)
                    await self._state.save(current_state)
                # self._task_queue.remove(self._current_task)
        else:
            response = "Task is already completed"
            self._task_index += 1
        return response, context

    async def execute_handler(self, task, context: Context, handler, transformer, **kwargs):
        response = None
        try:
            # Check if the handler is a function or a class with an execute method
            if callable(handler):
                response = await handler(task, context=context, **kwargs)
            else:
                response = await handler.execute(task, context=context, **kwargs)

            self._pilot_state = await self._state.serialize(handler) or {}
            if self._pilot_state.get('_status', TaskStatus.DONE) == TaskStatus.DONE:
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

    async def to_dict_state(self) -> dict:
        return {
            '_current_observation': self._current_observation,
            '_task_queue': self._task_queue,
            '_completed_tasks': self._completed_tasks,
            '_current_task': self._current_task,
            '_task_index': self._task_index,
            '_response': self._response,
            '_context': self._context,
            '_pilot_state': self._pilot_state
        }

    async def from_dict_state(self, state):
        print("from_dict_state", state)
        if state:
            self._current_observation = state.get('_current_observation', None)
            self._task_queue = state.get('_task_queue', [])
            self._completed_tasks = state.get('_completed_tasks', [])
            self._current_task = state.get('_current_task', None)
            self._task_index = state.get('_task_index', 0)
            self._response = state.get('_response', None)
            self._context = state.get('_context', Context())
            self._pilot_state = state.get('_pilot_state', {})

    async def to_pickle_state(self):
        return await self.to_dict_state()

    async def from_pickle_state(self, state):
        return await self.from_dict_state(state)

import logging

from superpilot.core.callback.manager.base import BaseCallbackManager
from superpilot.core.callback.manager.std_io import STDInOutCallbackManager
from superpilot.core.pilot.chain.base import BaseChain, HandlerType

from superpilot.core.ability import AbilityAction
from superpilot.core.context.schema import Context, Message
from superpilot.core.pilot.chain.strategy.observation_strategy import Observation
from superpilot.core.planning import TaskStatus, Task, LanguageModelResponse
from superpilot.core.state.base import BaseState, State
from superpilot.core.state.mixins import DictStateMixin, PickleStateMixin
from superpilot.core.state.pickle import PickleState


class SuperChain(BaseChain, DictStateMixin, PickleStateMixin):

    def __init__(
        self,
        logger: logging.Logger = logging.getLogger(__name__),
        state: BaseState = None,
        thread_id: str = None,
        callback: BaseCallbackManager = STDInOutCallbackManager(),
        **kwargs
    ):
        super().__init__(logger, **kwargs)
        self.logger = logger
        self._interaction = False

        # state vars
        self._current_observation = None
        self._task_queue = []
        self._completed_tasks = []
        self._current_task = None
        self._task_index = 0
        self._response = None
        self._context = Context()
        self._pilot_state = {}

        # utility vars
        self._callback = callback
        self.thread_id = thread_id

        # load the values from state
        if state is None:
            state = State()
        self._state = state

        self.task: Task = None

    # TODO add files and data and additional kwargs
    async def execute(self, objective: str | Message, context: Context = None, **kwargs):
        objective = await self.init_context(context, objective)

        # Splitting the observation and execution phases
        print('context given to chain', context)
        # state = await self._state.load()
        # await self._state.deserialize(self, state)
        kwargs['current_chain'] = self
        self._interaction = False
        # TODO handle _current_observation and _task_queue in context
        if not self._current_observation:
            self.task = Task.factory(objective.message)
            self._context.task = self.task
            while True:
                await self._callback.on_observation_start(**kwargs)
                observation_response = await self.observe(objective.message, self._context, **kwargs)
                ability_args = observation_response.content
                if ability_args.get("clarifying_question"):
                    hold = await self.handle_clarification(observation_response, ability_args, **kwargs)
                    if hold:
                        # TODO saveContext and continue from here
                        pass
                else:
                    observation = Observation(**observation_response.get_content())
                    break
            if not observation:
                return "Either observation or observer is not defined, please set observer in the chain.", self._context
            print("kwargs in chain", kwargs)
            await self._callback.on_observation(observation, **kwargs)

            # self._current_observation = observation
            # self._task_queue = observation.tasks
            planning_message = Message.add_planning_message(
                'Task Breakdown:\n' +
                '\n'.join([task.objective for task in observation.tasks])
            )
            self._context.add_message(planning_message)
            self._pilot_state = {}
            self._context.task.sub_tasks = observation.get_tasks()

        while self.task.active_task_idx < len(self.task.sub_tasks):
            await self.execute_next(objective, **kwargs)
            # TODO: interaction can be more  types, some may hault the execution and some may continue right after interaction immedatly (like..question and info)
            if self._context.interaction:
                break
        if self.task.active_task_idx == len(self.task.sub_tasks):
            print('resetting state', self.thread_id)
            # await self._state.save({})
            await self._callback.on_chain_complete(**kwargs)
            print("chain completed")
        return self._response, self._context

    async def init_context(self, context, objective):
        if not isinstance(objective, Message):
            objective = Message.add_user_message(objective)
            # TODO: add files and data to context
        if context is not None:
            context.add_message(objective)
            self._context = context
        else:
            self._context = Context.load_context(objective)
        return objective

    async def execute_next(self, objective, **kwargs):
        self._current_task = self.task.current_sub_task
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
                print("Pilot state: ", self._pilot_state)
                # await self._state.deserialize(handler, self._pilot_state)
                await self.execute_handler(handler, transformer, user_input=objective, **kwargs)
                if self._context.interaction:
                    self._current_task.status = TaskStatus.IN_PROGRESS
                    # current_state = await self._state.serialize(self)
                    # await self._state.save(current_state)
                    print("saving state task in progress", self.thread_id)
                    await self._callback.on_user_interaction(**kwargs)
                else:
                    self._current_task.status = TaskStatus.DONE
                    self.task.active_task_idx += 1
        else:
            self._response = "Task is already completed"
            self._task_index += 1

    async def execute_handler(self, handler, transformer, **kwargs):
        response = None
        try:
            # Check if the handler is a function or a class with an execute method
            if callable(handler):
                response = await handler(self._current_task, context=self._context, **kwargs)
            else:
                response = await handler.execute(self._current_task, context=self._context, **kwargs)

            # self._pilot_state = await self._state.serialize(handler) or {}
            if not self._context.interaction:
                # if isinstance(response, LanguageModelResponse):
                #     self._context.add_attachment(response.get_content())
                # elif isinstance(response, Context):
                #     self._context.extend(response)
                # elif isinstance(response, AbilityAction):
                #     pass
                if transformer:
                    self._response, self._context = transformer(data=self._current_task, response=response, context=self._context)

        except Exception as e:
            import traceback
            self.logger.error(f"Error in handler {handler.name()}: {e} {traceback.print_exc()}")
            
    async def handle_clarification(self, response, ability_args, **kwargs) -> bool:
        self._current_task.context.user_input.append(
            f"Assistant: {ability_args.get('clarifying_question')}"
        )
        question_message = Message.add_question_message(
            message=ability_args.get("clarifying_question")
        )
        self._context.add_message(question_message)
        user_input, hold = await self._callback.on_clarifying_question(
            question_message,
            self.task,
            response,
            self._context,
            **kwargs
        )
        if user_input:
            self._current_task.context.user_input.append(f"User: {user_input.message}")
            self._context.add_message(user_input)
        return hold

    async def observe(self, objective, context, **kwargs) -> LanguageModelResponse:
        observer = self.current_observer()
        if observer:
            try:
                return await observer.execute(objective, context, pilots=self.dump_pilots())
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

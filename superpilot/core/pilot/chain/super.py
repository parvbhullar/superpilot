import logging
from typing import Union

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
from superpilot.core.workspace import Workspace


class SuperChain(BaseChain):

    def __init__(
        self,
        state: BaseState = None,
        thread_id: str = None,
        context: Context = None,
        logger: logging.Logger = logging.getLogger(__name__),
        callback: BaseCallbackManager = STDInOutCallbackManager(),
        **kwargs
    ):
        super().__init__(logger, **kwargs)
        self._state = state or State()
        self._thread_id = thread_id
        self._context = context
        self.logger = logger
        self._callback = callback
        self.task: Task = None
        self._current_task: Task = None

    # TODO add files and data and additional kwargs
    async def execute(self, objective: Union[str, Message, Task], **kwargs):
        if isinstance(objective, Task):
            self.task = objective
        else:
            if isinstance(objective, str):
                objective = Message.add_user_message(objective)
            self._context.add_message(objective)

        self._context.interaction = False

        # TODO: user message bhejega to uss time pe new task banne se kese roke?
        if not self.task:
            task = self._context.current_task
            if not task:
                self.task = Task.factory(objective.message)
                self._context.tasks.append(self.task)
            else:
                self.task = task

        if not self.task.sub_tasks:
            if self.task.status == TaskStatus.BACKLOG:
                task_start_message = Message.add_task_start_message(f"Starting Task: '{objective.message}'")
                self._context.add_message(task_start_message)
            self.task.status = TaskStatus.IN_PROGRESS
            while True:
                await self._callback.on_observation_start(**kwargs)
                observation_response = await self.observe(objective.message, self._context, **kwargs)
                ability_args = observation_response.content.get("function_arguments", {})
                if ability_args.get("clarifying_question"):
                    hold = await self.handle_clarification(observation_response, ability_args, **kwargs)
                    if hold:
                        self._context.interaction = True
                        await self._state.save(self._context)
                        return
                else:
                    observation = Observation(**ability_args)
                    if not observation:
                        raise Exception("Either observation or observer is not defined, please set observer in the chain.")
                    print("kwargs in chain", kwargs)
                    await self._callback.on_observation(observation, **kwargs)
                    planning_message = Message.add_planning_message(
                        f'Pilot level Task Breakdown of "{objective.message}":\n' +
                        '\n'.join([f"'{task.objective}' will be done by {task.function_name} pilot" for task in observation.tasks])
                    )
                    self._context.add_message(planning_message)
                    self.task.sub_tasks = observation.get_tasks()
                    break

        while self.task.active_task_idx < len(self.task.sub_tasks):
            await self.execute_next(objective, **kwargs)
            if self._context.interaction:
                break
        if self.task.active_task_idx == len(self.task.sub_tasks):
            print('resetting state', self._thread_id)
            self._context.current_task.status = TaskStatus.DONE
            task_end_message = Message.add_task_end_message(f"Task Completed: '{objective.message}'")
            self._context.add_message(task_end_message)
            await self._state.save(self._context)
            await self._callback.on_chain_complete(**kwargs)
            print("chain completed")

    async def execute_next(self, objective, **kwargs):
        self._current_task = self.task.current_sub_task
        if self._current_task.status != TaskStatus.DONE:
            handler, transformer = self.current_handler(self._current_task.function_name)
            if handler is None:
                # TODO : Add a check to see if the task needs to be created as multiple tasks
                # return f"Handler named '{task_in_hand.function_name}' is not defined", context
                # TODO: Remove posibilty of null handler, or handle the situation...(dont start execution without confirming the flow from anther plan observer) - (planner, plan observer internal talks)
                self.logger.error(f"Handler named '{self._current_task.function_name}' is not defined")
                # TODO: need to be fixed, just increasing the task index to not to stuck in the same task
                self.task.active_task_idx += 1
            else:
                # TODO: there should be Pilot Task where we store the pilot Action?
                await self.execute_handler(handler, transformer, user_input=objective, **kwargs)
                if not self._context.interaction:
                    self._current_task.status = TaskStatus.DONE
                    self.task.active_task_idx += 1
        else:
            self._response = "Task is already completed"
            self.task.active_task_idx += 1

    async def execute_handler(self, handler, transformer, **kwargs):
        response = None
        try:
            # Check if the handler is a function or a class with an execute method
            if callable(handler):
                response = await handler(self._current_task, **kwargs)
            else:
                response = await handler.execute(self._current_task, **kwargs)

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
            self._context.add_message(user_input)
        return hold

    async def observe(self, objective, context, **kwargs) -> LanguageModelResponse:
        observer = self.current_observer()
        if observer:
            try:
                return await observer.execute(objective, context, pilots=self.dump_pilots(), task_objective=self.task.objective, **kwargs)
            except Exception as e:
                import traceback
                self.logger.error(f"Error in observer {observer.name()}: {e} {traceback.print_exc()}")
                return None
        return None


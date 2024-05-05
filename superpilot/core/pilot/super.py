from datetime import datetime
from typing import Union, List

from superpilot.core.ability import (
    AbilityRegistry,
    SuperAbilityRegistry, AbilityAction, Ability, )
from superpilot.core.callback.manager.base import BaseCallbackManager
from superpilot.core.callback.manager.std_io import STDInOutCallbackManager
from superpilot.core.configuration import Configurable
from superpilot.core.context.schema import Context, Message
from superpilot.core.environment import SimpleEnv, Environment
from superpilot.core.pilot.base import Pilot
from superpilot.core.pilot.settings import (
    PilotSystemSettings,
    PilotConfiguration,
    ExecutionNature,
)
from superpilot.core.planning import LanguageModelResponse
from superpilot.core.planning import SimplePlanner, Task, TaskStatus
from superpilot.core.planning.base import Planner
from superpilot.core.resource.model_providers import OpenAIModelName
from superpilot.core.resource.model_providers.factory import ModelProviderFactory, ModelConfigFactory
from superpilot.core.state.base import BaseState


class SuperPilot(Pilot, Configurable):
    default_settings = PilotSystemSettings(
        name="super_pilot",
        description="A super pilot.",
        configuration=PilotConfiguration(
            name="Entrepreneur-GPT",
            role=(
                "An AI designed to autonomously develop and run businesses with "
                "the sole goal of increasing your net worth."
            ),
            goals=[
                "Increase net worth",
                "Grow Twitter Account",
                "Develop and manage multiple businesses autonomously",
            ],
            cycle_count=0,
            max_task_cycle_count=3,
            creation_time="",
            execution_nature=ExecutionNature.AUTO,
        ),
    )

    def __init__(
        self,
        context: Context,
        settings: PilotSystemSettings,
        ability_registry: AbilityRegistry,
        planner: Planner,
        environment: SimpleEnv,
        callback: BaseCallbackManager,
        state: BaseState = None,
        **kwargs
    ):
        self._configuration = settings.configuration
        self._ability_registry = ability_registry
        self._logger = environment.get("logger")
        self._memory = environment.get("memory")
        # FIXME: Need some work to make this work as a dict of providers
        #  Getting the construction of the config to work is a bit tricky

        self._openai_provider = environment.get("model_providers")["openai"]
        self._planner = planner
        self._callback = callback
        self._workspace = environment.get("workspace")

        self._completed_tasks = []
        self._current_task: Task = None
        self._next_step_response: LanguageModelResponse = None
        self._context: Context = context
        self._state = state
        self.task: Task = None

    async def plan(self, task: Task, **kwargs):
        """Plan the next step for the pilot."""
        if self._configuration.execution_nature == ExecutionNature.SEQUENTIAL:
            tasks = []
            for ability in self._ability_registry.abilities():
                tasks.append(
                    Task(
                        objective=task.objective,
                        type=task.type,
                        priority=task.priority,
                        function_name=ability.name(),
                        ready_criteria=task.ready_criteria,
                        acceptance_criteria=task.acceptance_criteria,
                    )
                )
            self.task.add_plan(tasks)
        else:
            plan = await self._planner.plan(
                user_objective=task,
                functions=self._ability_registry.dump_abilities(),
            )
            if self._context.interaction:
                return
            tasks = plan.get_tasks()
            self.task.add_plan(tasks)
            planning_message = Message.add_planning_message(
                f'Ability Level Task Breakdown of task "{task.objective}":\n' + 
                '\n'.join([f"'{task.objective}' will be done by {task.function_name} ability" for task in tasks])
            )
            self._context.add_message(planning_message)
            # TODO: Should probably do a step to evaluate the quality of the generated tasks,
            #  and ensure that they have actionable ready and acceptance criteria
            # self._task_queue.extend(tasks)
            self.task.plan.sort(key=lambda t: t.priority)
        # self._task_queue[-1].context.status = TaskStatus.READY

    async def execute(self, objective: Union[str, Task, Message], *args, **kwargs):
        self._logger.info(f"Executing step {self._configuration.cycle_count}")

        if isinstance(objective, Task):
            self.task = objective
        else:
            if isinstance(objective, str):
                objective = Message.add_user_message(objective)
            self._context.add_message(objective)

        if not self.task:
            task = self._context.current_task
            if not task:
                self.task = Task.factory(objective.message)
                self._context.tasks.append(self.task)
            else:
                self.task = task

        if not self.task or not self.task.plan:
            if self.task.status == TaskStatus.BACKLOG:
                task_start_message = Message.add_task_start_message(f"'{self.task.objective}' task started")
                self._context.add_message(task_start_message)
            self.task.status = TaskStatus.IN_PROGRESS
            await self.plan(self.task)
            if self._context.interaction:
                return

        while self.task.active_task_idx < len(self.task.plan):
            await self.determine_next_step(*args, **kwargs)
            # TODO callback to take user input if required.
            ability_args = self._next_step_response.get("function_arguments", {})
            if ability_args.get("clarifying_question"):
                hold = await self.handle_clarification(ability_args, **kwargs)
                if hold:
                    self._context.interaction = True
                    return None
                continue
            # await self.update_task_status()
            # await self.update_task_queue()
            # if self._current_task.context.status != TaskStatus.DONE:
            #     await self.execute_next_step(*args, **kwargs)
            await self.execute_next_step(*args, **kwargs)

        if self.task.active_task_idx == len(self.task.plan):
            self.task.status = TaskStatus.DONE
            task_end_message = Message.add_task_end_message(f"'{self.task.objective}' task completed")
            self._context.add_message(task_end_message)

    async def handle_clarification(self, ability_args, **kwargs) -> bool:
        self._current_task.context.user_input.append(
            f"Assistant: {ability_args.get('clarifying_question')}"
        )
        question_message = Message.add_question_message(
            message=ability_args.get("clarifying_question")
        )
        self._context.add_message(question_message)
        user_input, hold = await self._callback.on_clarifying_question(
            question_message,
            self._current_task,
            self._next_step_response,
            self._context,
            **kwargs
        )
        if user_input:
            self._current_task.context.user_input.append(f"User: {user_input.message}")
            self._context.add_message(user_input)
        return hold

    async def reflect(self, *args, **kwargs):
        await self._planner.reflect(self._current_task, self._current_task.context)
        pass

    async def determine_next_step(self, *args, **kwargs):
        # if not self._task_queue:
        #     return {"response": "I don't have any tasks to work on right now."}

        # TODO: Maybe move config count to context as well
        self._configuration.cycle_count += 1
        self._current_task = self.task.current_sub_task
        self._logger.info(f"Working on task: {self._current_task}")
        # self._ability_registry.dump_abilities()
        task = await self._evaluate_task_and_add_context(self._current_task)
        next_response = await self._choose_next_step(
            task,
            [self._ability_registry.get_ability(self._current_task.function_name).dump()],
        )
        self._next_step_response = next_response

    async def execute_next_step(self, *args, **kwargs):
        ability_args = self._next_step_response.get("function_arguments", {})
        kwargs['action_objective'] = self._current_task.objective
        kwargs['callback'] = self._callback # TODO pass callback to ability registry
        # kwargs['thread_id'] = self.thread_id
        # Add context to ability arguments
        ability_action = await self._ability_registry.perform(
            self._next_step_response.get("function_name"), ability_args=ability_args, **kwargs
        )
        if ability_action.success:
            self._current_task.context.status = TaskStatus.DONE
            self.task.active_task_idx += 1
            # if self._current_task.context.status != TaskStatus.DONE:
            #     await self.execute_next_step(*args, **kwargs)
        # TODO: Take raw response and also summary
        execution_message = Message.add_execution_message(message=str(ability_action))
        self._context.add_message(execution_message)
        # ability_response = await ability(**self._next_step_response["ability_arguments"], **kwargs)
        await self._update_tasks_and_memory(ability_action)
        # if ability_action.success:
        self._current_task = None
        self._next_step_response = None

    async def update_task_queue(self):
        if self._current_task.context.status == TaskStatus.DONE:
            # self._completed_tasks.append(self._current_task)
            self.task.active_task_idx += 1
            # self._context.add_task(self._current_task)
        # else:
            # TODO insert the new task if required
            # self._task_queue.append(self._current_task)

    async def _evaluate_task_and_add_context(self, task: Task) -> Task:
        """Evaluate the task and add context to it."""
        if task.context.status == TaskStatus.IN_PROGRESS:
            # Nothing to do here
            return task
        else:
            self._logger.debug(f"Evaluating task {task} and adding relevant context.")
            # TODO: Look up relevant memories (need working memory system)
            # TODO: Evaluate whether there is enough information to start the task (language model call).
            task.context.enough_info = True
            task.context.status = TaskStatus.IN_PROGRESS
            return task

    async def _choose_next_step(self, task: Task, ability_schema: list[dict]) -> LanguageModelResponse:
        """Choose the next ability to use for the task."""
        self._logger.debug(f"Choosing next ability for task {task}.")
        # if task.context.cycle_count > self._configuration.max_task_cycle_count:
        #     # Don't hit the LLM, just set the next action as "breakdown_task" with an appropriate reason
        #     raise NotImplementedError
        # elif not task.context.enough_info:
        #     # Don't ask the LLM, just set the next action as "breakdown_task" with an appropriate reason
        #     raise NotImplementedError
        # else:
        next_response = await self._planner.next(
            task, ability_schema, context=self._context, function_name=self._current_task.function_name
        )
        return next_response

    async def _update_tasks_and_memory(self, ability_response: AbilityAction):
        self._current_task.context.cycle_count += 1
        self._current_task.context.prior_actions.append(ability_response)
        # TODO: Summarize new knowledge
        # TODO: store knowledge and summaries in memory and in relevant tasks
        # TODO: evaluate whether the task is complete
        # TODO update memory with the facts, insights and knowledge

        self._logger.info(f"Final response: {ability_response}")
        self._current_task.context.enough_info = True
        # self._current_task.update_memory(ability_response.get_memories())
        # print("Ability result", ability_result.result)

        # TaskStore.save_task_with_status(self._current_goal, status, stage)

    async def update_task_status(self):
        status = TaskStatus.IN_PROGRESS
        llm_status = self._next_step_response.content.get("task_status")
        if llm_status:
            status = TaskStatus(llm_status)
        self._current_task.context.status = status

    @classmethod
    def create(cls,
               context: Context,
               smart_model_name=OpenAIModelName.GPT4,
               fast_model_name=OpenAIModelName.GPT3,
               smart_model_temp=0.9,
               fast_model_temp=0.9,
               model_providers=None,
               pilot_config=None,
               abilities: List[Ability] = None,
               environment: Environment = None,
               planner: Planner = None,
               callback: BaseCallbackManager = STDInOutCallbackManager(),
               thread_id: str = None,
               state: BaseState = None,
               **kwargs
               ):

        models_config = ModelConfigFactory.get_models_config(
            smart_model_name=smart_model_name,
            fast_model_name=fast_model_name,
            smart_model_temp=smart_model_temp,
            fast_model_temp=fast_model_temp,
        )
        if model_providers is None:
            model_providers = ModelProviderFactory.load_providers()

        if environment is None:
            environment = SimpleEnv.create({})

        if planner is None:
            planner_settings = SimplePlanner.default_settings.copy()
            planner = SimplePlanner(
                context=context,
                settings=planner_settings,
                workspace=environment.get("workspace"),
                logger=environment.get("logger"),
                callback=callback,
                model_providers=model_providers,
                state=state
            )

        ability_registry = None
        if abilities is not None:
            allowed_abilities = []
            for ability_class in abilities:
                ability = ability_class(environment)
                allowed_abilities.append(ability)
            ability_registry = SuperAbilityRegistry(SuperAbilityRegistry.default_settings, environment)
            ability_registry._abilities = allowed_abilities

        settings = cls.default_settings.copy()
        settings.configuration = pilot_config

        pilot = cls(
            context=context,
            settings=settings,
            ability_registry=ability_registry,
            environment=environment,
            planner=planner,
            callback=callback,
            state=state,
            **kwargs
        )
        return pilot

    def __repr__(self):
        return "SuperPilot()"

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.name

    def dump(self) -> dict:
        pilot_config = self._configuration
        dump = {
            "name": pilot_config.name,
            "role": pilot_config.role,
            "goals": pilot_config.goals
        }
        return dump


def _prune_empty_dicts(d: dict) -> dict:
    """
    Prune branches from a nested dictionary if the branch only contains empty dictionaries at the leaves.

    Args:
        d: The dictionary to prune.

    Returns:
        The pruned dictionary.
    """
    pruned = {}
    for key, value in d.items():
        if isinstance(value, dict):
            pruned_value = _prune_empty_dicts(value)
            if (
                pruned_value
            ):  # if the pruned dictionary is not empty, add it to the result
                pruned[key] = pruned_value
        else:
            pruned[key] = value
    return pruned

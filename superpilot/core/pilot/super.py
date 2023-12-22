import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict, Tuple

from superpilot.core.ability import (
    AbilityAction,
    AbilityRegistry,
    SimpleAbilityRegistry, SuperAbilityRegistry, Ability,
)
from superpilot.core.callback.manager.base import BaseCallbackManager
from superpilot.core.callback.manager.std_io import STDInOutCallbackManager
from superpilot.core.context.schema import Context, Message
from superpilot.core.pilot.base import Pilot
from superpilot.core.pilot.settings import (
    PilotSettings,
    PilotSystemSettings,
    PilotConfiguration,
    PilotSystems,
    ExecutionAlgo, ExecutionNature
)
from superpilot.core.configuration import Configurable
from superpilot.core.memory import SimpleMemory
from superpilot.core.environment import SimpleEnv, Environment
from superpilot.core.planning import SimplePlannerLegacy, Task, TaskStatus, SimplePlanner, LanguageModelResponse
from superpilot.core.planning.base import Planner
from superpilot.core.plugin.simple import (
    PluginLocation,
    PluginStorageFormat,
    SimplePluginService,
)
from superpilot.core.resource.model_providers import OpenAIProvider, OpenAIModelName, ModelProviderName, \
    LanguageModelProvider
from superpilot.core.resource.model_providers.factory import ModelProviderFactory, ModelConfigFactory
from superpilot.core.workspace.simple import SimpleWorkspace


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
        settings: PilotSystemSettings,
        ability_registry: AbilityRegistry,
        planner: Planner,
        environment: SimpleEnv,
        callback: BaseCallbackManager,
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

        self._task_queue = []
        self._completed_tasks = []
        self._current_task = None
        self._next_step_response: LanguageModelResponse = None
        self._context: Context = None

    async def plan(self, user_objective: str, context: Context, **kwargs):
        """Plan the next step for the pilot."""
        # TODO: use context to determine what the next step should be
        plan = await self._planner.plan(
            user_objective=user_objective,
            functions=self._ability_registry.list_abilities(),
        )
        tasks = plan.get_tasks()
        self._context = context
        self._context.tasks = tasks

        # TODO: Should probably do a step to evaluate the quality of the generated tasks,
        #  and ensure that they have actionable ready and acceptance criteria

        self._task_queue.extend(tasks)
        self._task_queue.sort(key=lambda t: t.priority, reverse=True)
        self._task_queue[-1].context.status = TaskStatus.READY
        return plan.dict()

    async def execute(self, user_objective: str, context: Context, *args, **kwargs):
        self._logger.info(f"Executing step {self._configuration.cycle_count}")
        plan = await self.plan(user_objective, context)

        while self._task_queue:
            task, response = await self.determine_next_step(*args, **kwargs)
            # TODO callback to take user input if required.
            await self.execute_next_step(*args, **kwargs)

            # await self.reflect(*args, **kwargs)

    async def check_for_clarification(self, response, context, **kwargs) -> bool:
        self._current_task.context.user_input.append(
            f"Assistant: {response.get('clarifying_question')}")
        question_message = Message.add_question_message(
            message=response.get("clarifying_question")
        )
        self._context.add_message(question_message)
        user_input, hold = await self._callback.on_clarifying_question(
            question_message,
            self._current_task,
            response,
            context,
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
        if not self._task_queue:
            return {"response": "I don't have any tasks to work on right now."}

        self._configuration.cycle_count += 1
        task = self._task_queue.pop()
        self._logger.info(f"Working on task: {task}")

        task = await self._evaluate_task_and_add_context(task)
        next_response = await self._choose_next_step(
            task,
            self._ability_registry.dump_abilities(),
        )
        self._current_task = task
        self._next_step_response = next_response
        return self._current_task, self._next_step_response

    async def execute_next_step(self, *args, **kwargs):
        if self._next_step_response.get("clarifying_question"):
            hold = await self.check_for_clarification(self._next_step_response, self._context, **kwargs)
            if hold:
                # TODO save state and exit
                pass
            await self.update_task_queue()
            return

        ability_args = self._next_step_response.get("ability_arguments", {})
        kwargs['action_objective'] = self._next_step_response.get("task_objective", "")
        kwargs['callback'] = self._callback # TODO pass callback to ability registry
        # kwargs['thread_id'] = self.thread_id
        # Add context to ability arguments
        ability_response = await self._ability_registry.perform(
            self._next_step_response.get("next_ability"), ability_args=ability_args, **kwargs
        )
        # ability_response = await ability(**self._next_step_response["ability_arguments"], **kwargs)
        await self._update_tasks_and_memory(ability_response, self._next_step_response)

        await self.update_task_queue()
        self._current_task = None
        self._next_step_response = None

    async def update_task_queue(self):
        if self._current_task.context.status == TaskStatus.DONE:
            self._completed_tasks.append(self._current_task)
            # self._context.add_task(self._current_task)
        else:
            # TODO insert the new task if required
            self._task_queue.append(self._current_task)

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
        if task.context.cycle_count > self._configuration.max_task_cycle_count:
            # Don't hit the LLM, just set the next action as "breakdown_task" with an appropriate reason
            raise NotImplementedError
        elif not task.context.enough_info:
            # Don't ask the LLM, just set the next action as "breakdown_task" with an appropriate reason
            raise NotImplementedError
        else:
            next_response = await self._planner.next(
                task, ability_schema
            )
            return next_response

    async def _update_tasks_and_memory(self, ability_response: AbilityAction, response: LanguageModelResponse):
        self._current_task.context.cycle_count += 1
        self._current_task.context.prior_actions.append(ability_response)
        # TODO: Summarize new knowledge
        # TODO: store knowledge and summaries in memory and in relevant tasks
        # TODO: evaluate whether the task is complete
        # TODO update memory with the facts, insights and knowledge

        self._logger.info(f"Final response: {ability_response}")
        status = TaskStatus.IN_PROGRESS
        if response.content.get("task_status"):
            status = TaskStatus(response.content.get("task_status"))
        self._status = status
        self._current_task.context.status = status
        self._current_task.context.enough_info = True
        self._current_task.update_memory(ability_response.get_memories())
        # print("Ability result", ability_result.result)

        # TaskStore.save_task_with_status(self._current_goal, status, stage)

    @classmethod
    def create(cls,
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
                settings=planner_settings,
                workspace=environment.get("workspace"),
                logger=environment.get("logger"),
                callback=callback,
                model_providers=model_providers
            )

        ability_registry = None
        if abilities is not None:
            allowed_abilities = {}
            for ability in abilities:
                allowed_abilities[ability.name()] = ability.default_configuration
            ability_registry = SuperAbilityRegistry.factory(
                environment, allowed_abilities
            )

        settings = cls.default_settings.copy()
        settings.configuration = pilot_config

        pilot = cls(
            settings=settings,
            ability_registry=ability_registry,
            environment=environment,
            planner=planner,
            callback=callback,
            **kwargs
        )
        return pilot

    def __repr__(self):
        return "SuperPilot()"

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.name

    def dump(self) -> dict:
        dump = "PilotName: " + self._configuration.name + "\n"
        dump += "PilotRole: " + self._configuration.role + "\n"
        dump += "PilotGoals: " + "\n".join(self._configuration.goals) + "\n"
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

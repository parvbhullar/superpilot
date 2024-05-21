import asyncio
import logging
import platform
import time
from typing import List, Dict

import distro

from superpilot.core.ability import SuperAbilityRegistry, AbilityAction
from superpilot.core.ability.base import Ability
from superpilot.core.ability.base import AbilityRegistry
from superpilot.core.callback.manager.base import BaseCallbackManager
from superpilot.core.callback.manager.std_io import STDInOutCallbackManager
from superpilot.core.context.schema import Context
from superpilot.core.environment import Environment, SimpleEnv
from superpilot.core.pilot.chain.strategy.observation_strategy import Observation
from superpilot.core.pilot.settings import (
    ExecutionNature
)
from superpilot.core.pilot.settings import PilotConfiguration, ExecutionAlgo
from superpilot.core.pilot.task.base import TaskPilot, TaskPilotConfiguration
from superpilot.core.planning import strategies
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelResponse,
    Task, TaskStatus,
)
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
    PromptStrategyConfiguration,
)
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.plugin.utlis import load_class
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
    OpenAIModelName, OpenAIProvider,
)
from superpilot.core.resource.model_providers.factory import (
    ModelProviderFactory,
    ModelConfigFactory,
)


class SuperTaskPilot(TaskPilot):
    default_configuration = TaskPilotConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.flow.simple.SuperTaskPilot",
        ),
        pilot=PilotConfiguration(
            name="super_task_pilot",
            role=("An AI Pilot designed to complete simple tasks with "),
            goals=[
                "Complete simple tasks",
            ],
            cycle_count=0,
            max_task_cycle_count=3,
            creation_time="",
            execution_nature=ExecutionNature.AUTO,
        ),
        execution_nature=ExecutionNature.AUTO,
        prompt_strategy=strategies.NextAbility.default_configuration,
        # callbacks=[],  # TODO implement callback configuration
        models={
            LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                model_name=OpenAIModelName.GPT3,
                provider_name=ModelProviderName.OPENAI,
                temperature=0.9,
            ),
            LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                model_name=OpenAIModelName.GPT4_TURBO,
                provider_name=ModelProviderName.OPENAI,
                temperature=0.9,
            ),
        },
    )

    def __init__(
        self,
        ability_registry: AbilityRegistry,
        model_providers: Dict[ModelProviderName, LanguageModelProvider],
        callback: BaseCallbackManager = STDInOutCallbackManager(),
        configuration: TaskPilotConfiguration = default_configuration,
        thread_id: str = None,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        self._ability_registry = ability_registry

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        prompt_config = self._configuration.prompt_strategy.dict()
        location = prompt_config.pop("location", None)
        if location is not None:
            self._prompt_strategy = load_class(location, prompt_config)
        else:
            self._prompt_strategy = strategies.NextAbility(**prompt_config)

        self._callback = callback
        self.thread_id = thread_id

        self._task_queue = []
        self._completed_tasks = []

        self._current_observation = None
        self._next_step = None
        self._current_context = Context()
        self._parent = None

        self._current_task: Task = None
        self._status = TaskStatus.BACKLOG
        self._interaction = False

    # async def interaction_handler(self):

    async def execute(self, objective: str | Task, *args, **kwargs) -> Context:
        """Execute the task."""
        self._logger.debug(f"Executing task: {objective}")
        self._parent = kwargs.get("current_chain", None)
        self._interaction = False
        self._current_context = kwargs.get("context", self._current_context)
        print("Pilot state and context: ", self._current_context, self._current_task)
        if self._current_task is None:
            if isinstance(objective, str):
                # if task is not passed, one is created with default settings
                task = Task.factory(objective)
            else:
                task = objective
            self._current_task = task
            self._current_task.set_default_memory(self._current_context.to_list())
        else:
            user_input = kwargs.get("user_input", "")
            self._current_task.context.user_input.append(f"User: {user_input}")
            # self._current_task.context.user_interactions[-1].user_input = kwargs.get("user_input", "")
       
        # Add the context to default task memory to make use of it in ability execution
        
        # TODO: how to use passed context in task execution?
        if len(args) > 0:
            kwargs["context"] = args[0]

        while self._current_task.context.status != TaskStatus.DONE:
            # TODO: No need to pass task because already member of class
            await self.exec_abilities(**kwargs)
            if self._interaction:
                print("breaking from super pilot", self._interaction, self._current_task.context.status)
                break
            # messages = self._com_provider.receive()
            # if messages:
            #     self._logger.info(f"Message received: {message}")
            #     self._current_context.add(message)

            # TODO check if any user message is received and based on that interrupt the execution
            # or update the context

        # TODO: Use Ability actions to populate context?
        # TODO: we are overriding memories so this wll be the default ability response in most cases ( - aother way to improve context is keep the whole ability context when executing in pilot and pass only the last one as response)
        if self._current_task.context.prior_actions:
            return Context().add_content(self._current_task.context.prior_actions[-1].message)
        return Context()

    async def exec_abilities(self,  **kwargs) -> None:
        # TODO: Ability execution needs to be fixed for parallel and sequential execution
        if self._execution_nature == ExecutionNature.PARALLEL:
            tasks = [
                self.perform_ability(self._current_task, [ability.dump()], **kwargs)
                for ability in self._ability_registry.abilities()
            ]
            await asyncio.gather(*tasks)
            # res_list = await asyncio.gather(*tasks)
            # for response in res_list:
            #     ability_actions.append(response)
        elif self._execution_nature == ExecutionNature.AUTO:
            await self.perform_ability(
                self._current_task, self._ability_registry.dump_abilities(), **kwargs
            )
        else:
            # Execute for Sequential nature
            for ability in self._ability_registry.abilities():
                # print(res.content)
                await self.perform_ability(
                    self._current_task, [ability.dump()], **kwargs
                )
                # TODO add context to task prior actions as ability action.
                # task.

    async def perform_ability(
        self, task: Task, ability_schema: List[dict], **kwargs
    ) -> None:
        if self._execution_nature == ExecutionNature.AUTO:
            response = await self.determine_next_ability(
                task, ability_schema, **kwargs
            )
        else:
            response = await self.determine_exec_ability(
                task, ability_schema, **kwargs
            )

        if response.content.get("clarifying_question"):
            self._current_task.context.user_input.append(f"Assistant: {response.content.get('clarifying_question')}")
            user_input, hold = await self._callback.on_clarifying_question(
                response.content.get("clarifying_question"), self._current_task, response, self._current_context, self.thread_id, **kwargs
            )
            if user_input:
                self._current_task.context.user_input.append(f"User: {user_input}")
            self._interaction = hold
            return

        ability_args = response.content.get("ability_arguments", {})
        # TODO do a better implementation
        kwargs['callback'] = self._callback
        kwargs['action_objective'] = response.get("task_objective", "")
        # Add context to ability arguments
        ability_action = await self._ability_registry.perform(
            response.content["next_ability"], ability_args=ability_args, **kwargs
        )

        await self._update_tasks_and_memory(ability_action, response)

        # TODO : DO we need to ask question to user here? if
        # self._com_provider.send(message=ability_action.result)
        # Will put this task on hold and wait for user response
        # if task is on hold then we will store the current state of thread and wait for user response
        # wait for 5 minutes for user response

        # TODO: below section of code is doing nothing as of now
        if self._current_task.context.status == TaskStatus.DONE:
            # TODO: this queue is not used anywhere
            self._completed_tasks.append(self._current_task)
        else:
            # TODO: this queue is not used anywhere
            self._task_queue.append(self._current_task)
        # self._current_task = None  #TODO : Check if this is required
        self._next_step = None
        # TODO: Remove below line, only for testing purpose
        # self._interaction = True

    async def _update_tasks_and_memory(self, ability_result: AbilityAction, response: LanguageModelResponse):
        self._current_task.context.cycle_count += 1
        self._current_task.context.prior_actions.append(ability_result)
        # TODO: Summarize new knowledge
        # TODO: store knowledge and summaries in memory and in relevant tasks
        # TODO: evaluate whether the task is complete
        # TODO update memory with the facts, insights and knowledge

        self._logger.info(f"Final response: {ability_result}")
        status = TaskStatus.IN_PROGRESS
        if response.content.get("task_status"):
            status = TaskStatus(response.content.get("task_status"))
        self._status = status
        self._current_task.context.status = status
        self._current_task.context.enough_info = True
        self._current_task.update_memory(ability_result.get_memories())
        # print("Ability result", ability_result.result)

        # TaskStore.save_task_with_status(self._current_goal, status, stage)

    async def determine_exec_ability(
        self, task: Task, ability_schema: List[dict], **kwargs
    ) -> LanguageModelResponse:
        return await self.chat_with_model(
            self._prompt_strategy,
            task=task,
            ability_schema=ability_schema,
            **kwargs,
        )

    async def determine_next_ability(
        self, task: Task, ability_schema: List[dict], **kwargs
    ) -> LanguageModelResponse:
        return await self.chat_with_model(
            self._prompt_strategy,
            task=task,
            ability_schema=ability_schema,
            **kwargs,
        )

    async def chat_with_model(
        self,
        prompt_strategy: PromptStrategy,
        **kwargs,
    ) -> LanguageModelResponse:
        model_classification = prompt_strategy.model_classification
        model_configuration = self._configuration.models[model_classification].dict()
        self._logger.debug(f"Using model configuration: {model_configuration}")
        print(f"Using model configuration: {model_configuration}")
        del model_configuration["provider_name"]
        provider = self._providers[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(prompt_strategy)
        template_kwargs.update(kwargs)
        prompt = prompt_strategy.build_prompt(**template_kwargs)

        self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        print(f"Using prompt:\n{prompt}\n\n")
        response = await provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )
        # return LanguageModelResponse.model_validate(response.model_dump())
        return LanguageModelResponse.parse_obj(response.dict())


    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy):
        provider = self._providers[strategy.model_classification]
        template_kwargs = {
            "os_info": get_os_info(),
            "api_budget": provider.get_remaining_budget(),
            "current_time": time.strftime("%c"),
        }
        return template_kwargs

    def __repr__(self):
        return f"SuperTaskPilot({self._configuration})"

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.pilot.name

    def dump(self) -> dict:
        pilot_config = self._configuration.pilot
        dump = {
            "name": pilot_config.name,
            "role": pilot_config.role,
            "goals": pilot_config.goals
        }
        return dump

    async def to_dict_state(self) -> dict:
        return {
            '_current_task': self._current_task,
            '_interaction': self._interaction,
            '_status': self._status,
        }

    async def from_dict_state(self, state):
        if state:
            self._current_task = state.get('_current_task')
            self._interaction = state.get('_interaction', False)
            self._status = state.get('_status', TaskStatus.BACKLOG)

    async def to_pickle_state(self):
        return await self.to_dict_state()

    async def from_pickle_state(self, state):
        return await self.from_dict_state(state)

    @classmethod
    def factory(
            cls,
            ability_registry: AbilityRegistry,
            prompt_strategy: PromptStrategyConfiguration = None,
            model_providers: Dict[ModelProviderName, LanguageModelProvider] = None,
            execution_nature: ExecutionNature = None,
            models: Dict[LanguageModelClassification, LanguageModelConfiguration] = None,
            pilot_config: PilotConfiguration = None,
            location: PluginLocation = None,
            logger: logging.Logger = None,
            callback: BaseCallbackManager = STDInOutCallbackManager(),
            thread_id: str = None,
            **kwargs
    ) -> "SuperTaskPilot":
        # Initialize settings
        config = cls.default_configuration.copy()
        if location is not None:
            config.location = location
        if execution_nature is not None:
            config.execution_nature = execution_nature
        if prompt_strategy is not None:
            config.prompt_strategy = prompt_strategy
        if pilot_config is not None:
            config.pilot = pilot_config
        if models is not None:
            config.models = models

        # Use default logger if not provided
        if logger is None:
            logger = logging.getLogger(__name__)

        # Use empty dictionary for model_providers if not provided
        if model_providers is None:
            # Load Model Providers
            open_ai_provider = OpenAIProvider.factory()
            model_providers = {ModelProviderName.OPENAI: open_ai_provider}

        # Create and return SimpleTaskPilot instance
        return cls(
            ability_registry=ability_registry,
            configuration=config,
            model_providers=model_providers, 
            logger=logger,
            callback=callback,
            thread_id=thread_id,
        )

    @classmethod
    def create(cls,
               prompt_config=None,
               smart_model_name=OpenAIModelName.GPT4,
               fast_model_name=OpenAIModelName.GPT3,
               smart_model_temp=0.9,
               fast_model_temp=0.9,
               model_providers=None,
               pilot_config=None,
               abilities: List[Ability] = None,
               environment: Environment = None,
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

        ability_registry = None
        if abilities is not None:
            allowed_abilities = {}
            for ability in abilities:
                allowed_abilities[ability.name()] = ability.default_configuration
            ability_registry = SuperAbilityRegistry.factory(
                environment, allowed_abilities
            )

        pilot = cls.factory(
            ability_registry=ability_registry,
            prompt_strategy=prompt_config,
            model_providers=model_providers,
            models=models_config,
            pilot_config=pilot_config,
            callback=callback,
            thread_id=thread_id,
            **kwargs
        )
        return pilot


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info

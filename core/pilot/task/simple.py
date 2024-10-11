import logging
import platform
import time
from abc import ABC
from typing import Dict

import distro

from superpilot.core.callback.manager.base import BaseCallbackManager
from superpilot.core.pilot.settings import ExecutionNature
from superpilot.core.pilot.settings import PilotConfiguration
from superpilot.core.pilot.task.base import TaskPilot, TaskPilotConfiguration
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelResponse,
    Task,
)
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
    PromptStrategyConfiguration,
)
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.plugin.utlis import load_class
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
    OpenAIModelName,
    OpenAIProvider,
    OPEN_AI_MODELS,
)
from superpilot.core.resource.model_providers.factory import (
    ModelProviderFactory,
    ModelConfigFactory,
)
from superpilot.core.resource.model_providers.utils.token_counter import (
    count_string_tokens,
)
from superpilot.core.state.mixins import PickleStateMixin, DictStateMixin


class SimpleTaskPilot(TaskPilot, DictStateMixin, PickleStateMixin, ABC):
    """A class representing a pilot step."""

    default_configuration = TaskPilotConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.flow.simple.SuperTaskPilot",
        ),
        pilot=PilotConfiguration(
            name="simple_task_pilot",
            role=("An AI Pilot designed to complete simple tasks with "),
            goals=[
                "Complete simple tasks",
            ],
            cycle_count=0,
            max_task_cycle_count=3,
            creation_time="",
            execution_nature=ExecutionNature.AUTO,
        ),
        execution_nature=ExecutionNature.SIMPLE,
        prompt_strategy=SimplePrompt.default_configuration,
        models={
            LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                model_name=OpenAIModelName.GPT3,
                provider_name=ModelProviderName.OPENAI,
                temperature=0.9,
            ),
            LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                model_name=OpenAIModelName.GPT4,
                provider_name=ModelProviderName.OPENAI,
                temperature=0.9,
            ),
        },
    )

    def __init__(
        self,
        configuration: TaskPilotConfiguration = default_configuration,
        model_providers: Dict[ModelProviderName, LanguageModelProvider] = None,
        logger: logging.Logger = logging.getLogger(__name__),
        callback: BaseCallbackManager = None,
        thread_id: str = None,
    ) -> None:
        self._thread_id = thread_id
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        self._callback = callback

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        prompt_config = self._configuration.prompt_strategy.dict()
        location = prompt_config.pop("location", None)
        if location is not None:
            self._prompt_strategy = load_class(location, prompt_config)
        else:
            self._prompt_strategy = SimplePrompt(**prompt_config)

    async def execute(
        self, objective: str | Task, *args, **kwargs
    ) -> LanguageModelResponse:
        """Execute the task."""
        self._logger.debug(f"Executing task: {objective}")
        if isinstance(objective, str):
            # if task is not passed, one is created with default settings
            task = Task.factory(objective)
        else:
            task = objective
        if len(args) > 0:
            kwargs["context"] = args[0]
        context_res = await self.exec_task(task, **kwargs)
        return context_res

    # TODO: State may not be required in Simple Pilot, find a way to manage Cain flow without state
    async def to_dict_state(self) -> dict:
        pass

    async def from_dict_state(self, state):
        pass

    async def to_pickle_state(self):
        pass

    async def from_pickle_state(self, state):
        pass

    async def exec_task(self, task: Task, **kwargs) -> LanguageModelResponse:
        template_kwargs = task.generate_kwargs()
        template_kwargs.update(kwargs)
        return await self.chat_with_model(
            self._prompt_strategy,
            **template_kwargs,
        )

    async def chat_with_model(
        self,
        prompt_strategy: PromptStrategy,
        **kwargs,
    ) -> LanguageModelResponse:
        model_classification = prompt_strategy.model_classification
        model_configuration = self._configuration.models[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(prompt_strategy)
        kwargs.update(template_kwargs)
        prompt = prompt_strategy.build_prompt(
            model_name=model_configuration.model_name, **kwargs
        )
        # print("Prompt", prompt)
        model_configuration = self.choose_model(
            model_classification, model_configuration, prompt
        )

        model_configuration = model_configuration.dict()
        self._logger.debug(f"Using model configuration: {model_configuration}")
        del model_configuration["provider_name"]
        provider = self._providers[model_classification]
        if "response_format" in kwargs:
            model_configuration["response_format"] = kwargs["response_format"]

        self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        response = await provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            function_call=prompt.get_function_call(),
            req_res_callback=(
                self._callback.model_req_res_callback if self._callback else None
            ),
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )

        return LanguageModelResponse.parse_obj(response.dict())

    def choose_model(self, model_classification, model_configuration, prompt):
        if model_configuration.model_name not in [
            OpenAIModelName.GPT3,
            OpenAIModelName.GPT4,
        ]:
            return model_configuration
        current_tokens = count_string_tokens(
            str(prompt), model_configuration.model_name
        )
        print("Tokens", current_tokens)
        token_limit = OPEN_AI_MODELS[model_configuration.model_name].max_tokens
        completion_token_min_length = 1000
        send_token_limit = token_limit - completion_token_min_length
        if current_tokens > send_token_limit:
            if model_classification == LanguageModelClassification.FAST_MODEL:
                model_configuration.model_name = OpenAIModelName.GPT3_16K
            elif model_classification == LanguageModelClassification.SMART_MODEL:
                print("Using GPT4_TURBO")
                model_configuration.model_name = OpenAIModelName.GPT4_TURBO
        return model_configuration

    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy):
        provider = self._providers[strategy.model_classification]
        template_kwargs = {
            "os_info": get_os_info(),
            "api_budget": provider.get_remaining_budget(),
            "current_time": time.strftime("%c"),
        }
        return template_kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self._configuration.__str__()

    def name(self) -> str:
        """The name of the ability."""
        return self._configuration.pilot.name

    def dump(self) -> dict:
        pilot_config = self._configuration.pilot
        dump = {
            "name": pilot_config.name,
            "role": pilot_config.role,
            "goals": pilot_config.goals,
        }
        return dump

    @classmethod
    def factory(
        cls,
        prompt_strategy: PromptStrategyConfiguration = None,
        model_providers: Dict[ModelProviderName, LanguageModelProvider] = None,
        execution_nature: ExecutionNature = None,
        models: Dict[LanguageModelClassification, LanguageModelConfiguration] = None,
        pilot_config: PilotConfiguration = None,
        location: PluginLocation = None,
        logger: logging.Logger = None,
        callback: BaseCallbackManager = None,
        thread_id: str = None,
    ) -> "SimpleTaskPilot":
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
            configuration=config,
            model_providers=model_providers,
            logger=logger,
            callback=callback,
            thread_id=thread_id,
        )

    @classmethod
    def create(
        cls,
        prompt_config,
        smart_model_name=OpenAIModelName.GPT4,
        fast_model_name=OpenAIModelName.GPT3,
        smart_model_temp=0.9,
        fast_model_temp=0.9,
        model_providers=None,
        pilot_config=None,
        callback: BaseCallbackManager = None,
        thread_id: str = None,
    ):
        models_config = ModelConfigFactory.get_models_config(
            smart_model_name=smart_model_name,
            fast_model_name=fast_model_name,
            smart_model_temp=smart_model_temp,
            fast_model_temp=fast_model_temp,
        )
        if model_providers is None:
            model_providers = ModelProviderFactory.load_providers()

        pilot = cls.factory(
            prompt_strategy=prompt_config,
            model_providers=model_providers,
            models=models_config,
            pilot_config=pilot_config,
            callback=callback,
            thread_id=thread_id,
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

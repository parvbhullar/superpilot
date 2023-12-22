import logging
import platform
import distro
import time
from abc import ABC

from superpilot.core.pilot.task.base import TaskPilot
from superpilot.core.pilot.task.settings import ModelTaskPilotConfiguration
from superpilot.core.planning.strategies.model import ModelPromptStrategy
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import LanguageModelResponse
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    PromptStrategyConfiguration,
)
from superpilot.core.plugin.utlis import load_class
from superpilot.core.resource.model_providers import ModelProviderName, OpenAIModelName
from superpilot.core.resource.model_providers.factory import load_model_provider


class ModelTaskPilot(TaskPilot, ABC):
    """A class representing a pilot step."""

    default_configuration = ModelTaskPilotConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.ModelTaskPilot",
        ),
        model_provider=LanguageModelConfiguration(
            model_name=OpenAIModelName.GPT3,
            provider_name=ModelProviderName.OPENAI,
            temperature=0.9,
        ),
    )

    def __init__(
        self,
        configuration: ModelTaskPilotConfiguration = default_configuration,
        model_provider: LanguageModelConfiguration = default_configuration.model_provider,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self._logger = logger
        self._configuration = configuration
        self._model_provider = model_provider
        prompt_config = (
            self._configuration.prompt_strategy.dict()
            if self._configuration.prompt_strategy
            else {}
        )
        location = prompt_config.pop("location", None)
        if location is not None:
            self._prompt_strategy = load_class(location, prompt_config)
        else:
            self._prompt_strategy = ModelPromptStrategy(**prompt_config)

    async def execute(
        self, objective: str, message_history=[], *args, **kwargs
    ) -> LanguageModelResponse:
        """Execute the task."""
        prompt_strategy = self._prompt_strategy
        response = await self.chat_with_model(
            prompt_strategy, user_input=objective, message_history=message_history
        )
        return response

    async def chat_with_model(
        self,
        prompt_strategy: PromptStrategy,
        **kwargs,
    ) -> LanguageModelResponse:
        model_configuration = self._model_provider
        provider = load_model_provider(model_configuration.provider_name)
        template_kwargs = self._make_template_kwargs_for_strategy(
            prompt_strategy, provider
        )
        kwargs.update(template_kwargs)
        prompt = prompt_strategy.build_prompt(
            model_name=model_configuration.model_name, **kwargs
        )

        model_configuration = model_configuration.dict()
        del model_configuration["provider_name"]
        self._logger.debug(f"Using model configuration: {model_configuration}")

        self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        response = await provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            function_call=prompt.get_function_call(),
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )

        return LanguageModelResponse.parse_obj(response.dict())

    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy, provider):
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

    def dump(self):
        return super().dump()

    @classmethod
    def factory(
        cls,
        prompt_strategy: PromptStrategyConfiguration = None,
        model_provider: LanguageModelConfiguration = None,
        location: PluginLocation = None,
        logger: logging.Logger = None,
    ) -> "ModelTaskPilot":
        # Initialize settings
        config = cls.default_configuration.copy()
        if location is not None:
            config.location = location
        if prompt_strategy is not None:
            config.prompt_strategy = prompt_strategy
        if logger is None:
            logger = logging.getLogger(__name__)
        if model_provider is None:
            open_ai_provider = LanguageModelConfiguration(
                model_name=OpenAIModelName.GPT3,
                provider_name=ModelProviderName.OPENAI,
                temperature=0.9,
            )

            model_provider = open_ai_provider

        return cls(configuration=config, model_provider=model_provider, logger=logger)


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info

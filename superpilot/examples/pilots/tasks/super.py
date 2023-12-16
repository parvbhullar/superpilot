import logging
from typing import Dict

from superpilot.core.pilot.settings import ExecutionNature
from superpilot.core.pilot.task.base import TaskPilotConfiguration
from superpilot.core.ability.base import AbilityRegistry
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.planning import strategies
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
)
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.examples.pilots.tasks.base import BaseTaskPilot


class SuperTaskPilot(BaseTaskPilot):
    default_configuration = TaskPilotConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.SuperTaskPilot",
        ),
        execution_nature=ExecutionNature.SEQUENTIAL,
        prompt_strategy=strategies.NextAbility.default_configuration,
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
        configuration: TaskPilotConfiguration = default_configuration,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self._logger = logger
        self._configuration = configuration
        self._execution_nature = configuration.execution_nature
        self._ability_registry = ability_registry

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        self._prompt_strategy = strategies.NextAbility(
            **self._configuration.prompt_strategy.dict()
        )

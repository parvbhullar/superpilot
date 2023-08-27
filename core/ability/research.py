import logging
from typing import Dict, List

from superpilot.core.ability.base import Ability, AbilityConfiguration, AbilityRegistry
from superpilot.core.ability.builtins import RESEARCH_ABILITIES
from superpilot.core.ability.schema import AbilityAction
from superpilot.core.configuration import (
    Configurable,
    SystemConfiguration,
    SystemSettings,
)
from superpilot.core.memory.base import Memory
from superpilot.core.plugin.research import ResearchPluginService
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
)
from superpilot.core.workspace.base import Workspace


class AbilityRegistryConfiguration(SystemConfiguration):
    """Configuration for the AbilityRegistry subsystem."""

    abilities: Dict[str, AbilityConfiguration]


class AbilityRegistrySettings(SystemSettings):
    configuration: AbilityRegistryConfiguration


class ResearchAbilityRegistry(AbilityRegistry, Configurable):
    default_settings = AbilityRegistrySettings(
        name="research_ability_registry",
        description="A research ability registry.",
        configuration=AbilityRegistryConfiguration(
            abilities={
                ability_name: ability.default_configuration
                for ability_name, ability in RESEARCH_ABILITIES.items()
            },
        ),
    )

    def __init__(
        self,
        settings: AbilityRegistrySettings,
        logger: logging.Logger,
        memory: Memory,
        workspace: Workspace,
        model_providers: Dict[ModelProviderName, LanguageModelProvider],
    ):
        self._configuration = settings.configuration
        self._logger = logger
        self._memory = memory
        self._workspace = workspace
        self._model_providers = model_providers
        self._abilities = []
        for (
            ability_name,
            ability_configuration,
        ) in self._configuration.abilities.items():
            self.register_ability(ability_name, ability_configuration)

    def register_ability(
        self, ability_name: str, ability_configuration: AbilityConfiguration
    ) -> None:
        ability_class = ResearchPluginService.get_plugin(ability_configuration.location)
        ability_args = {
            "logger": self._logger.getChild(ability_name),
            "configuration": ability_configuration,
        }
        if ability_configuration.packages_required:
            # TODO: Check packages are installed and maybe install them.
            pass
        if ability_configuration.memory_provider_required:
            ability_args["memory"] = self._memory
        if ability_configuration.workspace_required:
            ability_args["workspace"] = self._workspace
        if ability_configuration.language_model_required:
            ability_args["language_model_provider"] = self._model_providers[
                ability_configuration.language_model_required.provider_name
            ]
        ability = ability_class(**ability_args)
        self._abilities.append(ability)

    def list_abilities(self) -> List[str]:
        return [
            f"{ability.name()}: {ability.description()}" for ability in self._abilities
        ]

    def dump_abilities(self) -> List[dict]:
        return [ability.dump() for ability in self._abilities]

    def get_ability(self, ability_name: str) -> Ability:
        for ability in self._abilities:
            if ability.name() == ability_name:
                return ability
        raise ValueError(f"Ability '{ability_name}' not found.")

    async def perform(self, ability_name: str, **kwargs) -> AbilityAction:
        ability = self.get_ability(ability_name)
        return await ability(**kwargs)

import logging
from typing import Dict, List

from superpilot.core.ability.base import Ability, AbilityConfiguration, AbilityRegistry
from superpilot.core.ability.builtins import BUILTIN_ABILITIES
from superpilot.core.ability.schema import AbilityAction
from superpilot.core.configuration import (
    Configurable,
    SystemConfiguration,
    SystemSettings,
)
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.plugin.simple import SimplePluginService
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
)
from superpilot.core.workspace.base import Workspace
from superpilot.core.environment import Environment


class AbilityRegistryConfiguration(SystemConfiguration):
    """Configuration for the AbilityRegistry subsystem."""

    abilities: Dict[str, AbilityConfiguration]


class AbilityRegistrySettings(SystemSettings):
    configuration: AbilityRegistryConfiguration


class SuperAbilityRegistry(AbilityRegistry, Configurable):
    default_settings = AbilityRegistrySettings(
        name="super_ability_registry",
        description="A super ability registry.",
        configuration=AbilityRegistryConfiguration(
            abilities={
                ability_name: ability.default_configuration
                for ability_name, ability in BUILTIN_ABILITIES.items()
            },
        ),
    )

    def __init__(
        self,
        settings: AbilityRegistrySettings,
        environment: Environment,
    ):

        self._configuration = settings.configuration
        self._environment = environment
        self._logger = environment.get("logger")
        self._memory = environment.get("memory")
        self._workspace = environment.get("workspace")
        self._model_providers = environment.get("model_providers")
        print("model_providers", self._model_providers)
        self._abilities = []
        for (
            ability_name,
            ability_configuration,
        ) in self._configuration.abilities.items():
            self.register_ability(ability_name, ability_configuration)

    def register_ability(
        self, ability_name: str, ability_configuration: AbilityConfiguration
    ) -> None:
        ability_class = SimplePluginService.get_plugin(ability_configuration.location)
        ability_args = {
            "configuration": ability_configuration,
        }
        if ability_configuration.packages_required:
            # TODO: Check packages are installed and maybe install them.
            pass
        system_parameters = ability_class.__init__.__annotations__
        for parameter_name in system_parameters:
            if parameter_name not in ability_args and parameter_name != 'environment':
                ability_args[parameter_name] = self._environment.get(parameter_name)
        if 'environment' in system_parameters:
            ability_args['environment'] = self._environment
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
        print("Perform Ability: ", ability_name, kwargs)
        response = await ability(**kwargs)

        ability_action = AbilityAction()
        ability_action.executed = True
        ability_action.message = "Ability executed"
        # ability_action.wait_for_user = ability.wait()
        ability_action.add_knowledge(response)
        return ability_action

    def abilities(self) -> List[Ability]:
        return self._abilities


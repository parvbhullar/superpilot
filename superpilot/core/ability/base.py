import abc
from pprint import pformat
from typing import ClassVar, List
import logging
import inflection
from pydantic import Field

from superpilot.core.ability.schema import AbilityAction
from superpilot.core.configuration import SystemConfiguration
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.resource.model_providers import (
    LanguageModelMessage, LanguageModelFunction,
)
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from typing import Callable, ClassVar, List, Union
from superpilot.core.configuration.schema import (
    SystemConfiguration,
    SystemSettings,
    UserConfigurable,
)


class AbilityConfiguration(SystemConfiguration):
    """Struct for model configuration."""
    from superpilot.core.plugin.base import PluginLocation

    location: PluginLocation
    packages_required: List[str] = Field(default_factory=list)
    language_model_required: LanguageModelConfiguration = None
    memory_provider_required: bool = False
    workspace_required: bool = False

    @classmethod
    def factory(
            cls,
            location_route: str = "superpilot.core.builtins.QueryLanguageModel",
            model_name: str = OpenAIModelName.GPT3,
            provider_name: str = ModelProviderName.OPENAI,
            temperature: str = 0.9,
            memory_provider_required: bool = False,
            workspace_required: bool = False,
    ) -> "AbilityConfiguration":
        return AbilityConfiguration(
            location=PluginLocation(
                storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                storage_route=location_route,
            ),
            language_model_required=LanguageModelConfiguration(
                model_name=model_name,
                provider_name=provider_name,
                temperature=temperature,
            ),
            memory_provider_required=memory_provider_required,
            workspace_required=workspace_required,
        )


class Ability(abc.ABC):
    """A class representing an pilot ability."""

    default_configuration: ClassVar[AbilityConfiguration]

    _summary: str = None

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

    @classmethod
    @abc.abstractmethod
    def description(cls) -> str:
        """A detailed description of what the ability does."""
        ...

    @classmethod
    @abc.abstractmethod
    def arguments(cls) -> dict:
        """A dict of arguments in standard json schema format."""
        ...

    @classmethod
    def required_arguments(cls) -> List[str]:
        """A list of required arguments."""
        return []

    @property
    def summary(self) -> str:
        """A summary of the ability result."""
        return self._summary

    @abc.abstractmethod
    async def __call__(self, *args, **kwargs) -> AbilityAction:
        ...

    def __str__(self) -> str:
        return pformat(self.dump)

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

    def dump(self) -> dict:
        return {
            "name": self.name(),
            "description": self.description(),
            "parameters": {
                "type": "object",
                "properties": self.arguments(),
                "required": self.required_arguments(),
            },
        }

    @classmethod
    def create_ability(
            cls,
            ability_type: type,  # Assuming you pass the Class itself
            logger: logging.Logger,
            configuration: AbilityConfiguration,
    ) -> "Ability":
        # Instantiate and return Ability
        return ability_type(logger=logger, configuration=configuration)


class AbilityRegistry(abc.ABC):
    @abc.abstractmethod
    def register_ability(
        self, ability_name: str, ability_configuration: AbilityConfiguration
    ) -> None:
        ...

    @abc.abstractmethod
    def list_abilities(self) -> List[str]:
        ...

    @abc.abstractmethod
    def abilities(self) -> List[Ability]:
        ...

    @abc.abstractmethod
    def dump_abilities(self) -> List[dict]:
        ...

    @abc.abstractmethod
    def get_ability(self, ability_name: str) -> Ability:
        ...

    @abc.abstractmethod
    async def perform(self, ability_name: str, ability_args: dict, **kwargs) -> AbilityAction:
        ...

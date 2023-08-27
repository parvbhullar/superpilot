import abc
from pprint import pformat
from typing import ClassVar, List

import inflection
from pydantic import Field

from superpilot.core.ability.schema import AbilityAction
from superpilot.core.configuration import SystemConfiguration
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.planning.simple import PromptStrategy
from superpilot.core.resource.model_providers import (
    LanguageModelMessage, LanguageModelFunction,
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
    prompt_strategy: PromptStrategy = None
    memory_provider_required: bool = False
    workspace_required: bool = False


class Ability(abc.ABC):
    """A class representing an pilot ability."""

    default_configuration: ClassVar[AbilityConfiguration]

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

    @abc.abstractmethod
    async def __call__(self, *args, **kwargs) -> AbilityAction:
        ...

    def __str__(self) -> str:
        return pformat(self.dump)

    async def chat_with_model(self,
        model_prompt: List[LanguageModelMessage],
        functions: List[LanguageModelFunction] = [],
        completion_parser: Callable[[str], dict] = None,
        **kwargs
    ) -> List[str]:
        model_response = await self._language_model_provider.create_language_completion(
            model_prompt=model_prompt,
            functions=functions,
            model_name=self._configuration.language_model_required.model_name,
            completion_parser=completion_parser or self._parse_response,
        )
        return model_response

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
    async def perform(self, ability_name: str, **kwargs) -> AbilityAction:
        ...

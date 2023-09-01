import logging
from typing import Dict, List, Callable

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
from superpilot.core.workspace.base import Workspace
from superpilot.core.environment import Environment
from superpilot.core.planning import PromptStrategy
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.resource.model_providers import (
    LanguageModelMessage,
    LanguageModelProvider,
    LanguageModelFunction,
    MessageRole,
    ModelProviderName,
    OpenAIModelName,
)


class SuperAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.ability.SuperAbility",
        ),
        language_model_required=LanguageModelConfiguration(
            model_name=OpenAIModelName.GPT3,
            provider_name=ModelProviderName.OPENAI,
            temperature=0.9,
        ),
    )

    def __init__(
            self,
            logger: logging.Logger,
            configuration: AbilityConfiguration,
            language_model_provider: LanguageModelProvider,
            prompt_strategy: PromptStrategy,
    ):
        self._logger = logger
        self._configuration = configuration
        self._language_model_provider = language_model_provider
        self._prompt_strategy = prompt_strategy

    @classmethod
    def description(cls) -> str:
        return "Create a new ability by writing python code."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "ability_name": {
                "type": "string",
                "description": "A meaningful and concise name for the new ability.",
            },
            "description": {
                "type": "string",
                "description": "A detailed description of the ability and its uses, including any limitations.",
            },
            "arguments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the argument.",
                        },
                        "type": {
                            "type": "string",
                            "description": "The type of the argument. Must be a standard json schema type.",
                        },
                        "description": {
                            "type": "string",
                            "description": "A detailed description of the argument and its uses.",
                        },
                    },
                },
                "description": "A list of arguments that the ability will accept.",
            },
            "required_arguments": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "The names of the arguments that are required.",
                },
                "description": "A list of the names of the arguments that are required.",
            },
            "package_requirements": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "The of the Python package that is required to execute the ability.",
                },
                "description": "A list of the names of the Python packages that are required to execute the ability.",
            },
            "code": {
                "type": "string",
                "description": "The Python code that will be executed when the ability is called.",
            },
        }

    @classmethod
    def required_arguments(cls) -> List[str]:
        return ["ability_name", "description", "arguments", "required_arguments", "package_requirements", "code"]

    async def __call__(
            self,
            ability_name: str,
            description: str,
            arguments: List[dict],
            required_arguments: List[str],
            package_requirements: List[str],
            code: str,
    ) -> AbilityAction:
        breakpoint()

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

    @classmethod
    def create_new_ability(cls, logger: logging.Logger,
                           configuration: AbilityConfiguration) -> "SuperAbility":
        return cls(logger, configuration)
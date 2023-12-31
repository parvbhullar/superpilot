import logging
from typing import List

from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.ability.schema import AbilityAction
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    LanguageModelMessage,
    LanguageModelProvider,
    MessageRole,
    ModelProviderName,
    OpenAIModelName,
)


class QueryLanguageModel(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.ability.builtins.QueryLanguageModel",
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
    ):
        self._logger = logger
        self._configuration = configuration
        self._language_model_provider = language_model_provider

    @classmethod
    def description(cls) -> str:
        return "Query a language model. A query should be a question and any relevant context."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "query": {
                "type": "string",
                "description": "A query for a language model. A query should contain a question and any relevant context.",
            },
        }

    @classmethod
    def required_arguments(cls) -> List[str]:
        return ["query"]

    async def __call__(self, query: str) -> AbilityAction:
        messages = [
            LanguageModelMessage(
                content=query,
                role=MessageRole.USER,
            ),
        ]
        model_response = await self._language_model_provider.create_language_completion(
            model_prompt=messages,
            functions=[],
            model_name=self._configuration.language_model_required.model_name,
            completion_parser=self._parse_response,
        )
        return AbilityAction(
            ability_name=self.name(),
            ability_args={"query": query},
            success=True,
            message=model_response.content['content'],
        )

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

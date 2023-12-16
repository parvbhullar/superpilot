from typing import List
import logging
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.planning.strategies.summarizer_strategy import SummarizerStrategy
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
    OpenAIProvider,
)
from superpilot.framework.tools.summarizer import Summarizer
from superpilot.core.environment import Environment
from superpilot.core.configuration import Config
import asyncio


class TextSummarizeAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.framework.abilities.text_summarise.TextSummarizeAbility",
        ),
        language_model_required=LanguageModelConfiguration(
            model_name=OpenAIModelName.GPT3_16K,
            provider_name=ModelProviderName.OPENAI,
            temperature=0.9,
        ),
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
        prompt_strategy: SummarizerStrategy = None,
    ):
        self._configuration = configuration
        self._logger: logging.Logger = environment.get("logger")
        self._env_config: Config = environment.get("env_config")
        self._language_model_provider: OpenAIProvider = environment.get(
            "model_providers"
        ).get(configuration.language_model_required.provider_name)
        if prompt_strategy is None:
            prompt_strategy = SummarizerStrategy(
                model_classification=SummarizerStrategy.default_configuration.model_classification,
                system_prompt=SummarizerStrategy.default_configuration.system_prompt,
                user_prompt_template=SummarizerStrategy.default_configuration.user_prompt_template,
            )
        self._prompt_strategy = prompt_strategy

    @classmethod
    def description(cls) -> str:
        return (
            "Summarize information from the content list passed based on asked query."
        )

    @classmethod
    def arguments(cls) -> dict:
        return {
            "content": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "Additional context to refine the search and summarize the results.",
                },
                "description": "Contextual information to guide the search and summarization.",
            },
            "query": {
                "type": "string",
                "description": "The query to summarize the content of.",
            },
            "system_text": {
                "type": "string",
                "description": "System text to define the requirements and format of the summarization.",
                "default": "SUMMARIZE_SYSTEM_PROMPT",
            },
        }

    @classmethod
    def required_arguments(cls) -> List[str]:
        """A list of required arguments."""
        return ["content", "query"]

    async def __call__(
        self,
        content: List[str],
        query: str,
        system_text: str = "SUMMARIZE_SYSTEM",
        **kwargs
    ) -> Context:
        # Summarizing the text with links
        tasks = [
            Summarizer().run(response, query) for i, response in enumerate(content)
        ]
        # Gather the results as they become available
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        # con
        # text_summary = "\n".join(responses)
        text_summary = ""
        for response in responses:
            if response and not isinstance(response, Exception):
                text_summary += response + "\n"

        template_kwargs = {
            "content": text_summary,
            "question": query,
        }
        prompt = self._prompt_strategy.build_prompt(**template_kwargs)

        model_response = await self._language_model_provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            completion_parser=self._parse_response,
            model_name=self._configuration.language_model_required.model_name,
        )
        # print(model_response)
        text_summary = model_response.content["content"]
        return Context([Content.add_content_item(text_summary, ContentType.TEXT)])

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

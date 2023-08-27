from typing import List
import logging
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.ability.schema import AbilityAction
from superpilot.core.context.schema import Content, ContentType
from superpilot.core.planning import strategies
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
    OpenAIProvider,
)
from superpilot.framework.tools.search_engine import SearchEngine, SearchEngineType
from superpilot.framework.tools.web_browser import WebBrowserEngine
from superpilot.framework.tools.summarizer import Summarizer
from superpilot.framework.config import Config
import asyncio


class GoogleSearch(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.ability.builtins.GoogleSearch",
        ),
        language_model_required=LanguageModelConfiguration(
            model_name=OpenAIModelName.GPT3_16K,
            provider_name=ModelProviderName.OPENAI,
            temperature=0.9,
        ),
    )

    def __init__(
        self,
        settings: Config = Config(),
        configuration: AbilityConfiguration = default_configuration,
        language_model_provider=OpenAIProvider(),
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self._logger = logger
        self._configuration = configuration
        self._settings = settings
        self._language_model_provider = language_model_provider
        self._search_engine = SearchEngine(SearchEngineType.DIRECT_GOOGLE)
        prompt_strategy = strategies.SummarizerStrategy(
            model_classification=strategies.SummarizerStrategy.default_configuration.model_classification,
            system_prompt=strategies.SummarizerStrategy.default_configuration.system_prompt,
            user_prompt_template=strategies.SummarizerStrategy.default_configuration.user_prompt_template,
        )
        self._configuration.prompt_strategy = prompt_strategy

    @classmethod
    def description(cls) -> str:
        return (
            "Search and summarize information from the internet using search engines."
        )

    @classmethod
    def arguments(cls) -> dict:
        return {
            "query": {
                "type": "string",
                "description": "The query to search for on the internet.",
            },
            "context": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "Additional context to refine the search and summarize the results.",
                },
                "description": "Contextual information to guide the search and summarization.",
                "default": [],
            },
            "system_text": {
                "type": "string",
                "description": "System text to define the requirements and format of the search and summarization.",
                "default": "SEARCH_AND_SUMMARIZE_SYSTEM",
            },
        }

    async def __call__(
        self,
        query: str,
        context: List[str] = [],
        system_text: str = "SEARCH_AND_SUMMARIZE_SYSTEM",
    ) -> Content:
        no_google = (
            not self._settings.google_api_key
            or "YOUR_API_KEY" == self._settings.google_api_key
        )
        no_serpapi = (
            not self._settings.serp_api_key
            or "YOUR_API_KEY" == self._settings.serp_api_key
        )
        # no_serper = not self._configuration.serper_api_key or 'YOUR_API_KEY' == self._configuration.serper_api_key

        if no_serpapi and no_google:
            self._logger.warning(
                "Configure one of SERPAPI_API_KEY, SERPER_API_KEY, GOOGLE_API_KEY to unlock full feature"
            )
            return ""

        # logger.debug(query)
        rsp = await self._search_engine.run(query)
        if not rsp:
            self._logger.error("empty rsp...")
            return Content.add_content_item("Empty Response", ContentType.TEXT)

        self._logger.info(rsp)

        # Scraping the links
        new_search_urls = [link["link"] for link in rsp if link]
        # Create a list to hold the coroutine objects
        tasks = [WebBrowserEngine().run(url) for url in new_search_urls]
        # Gather the results as they become available
        text_responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Summarizing the text with links
        tasks = [
            Summarizer().run(response, query, new_search_urls[i])
            for i, response in enumerate(text_responses)
        ]
        # Gather the results as they become available
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        # con
        text_summary = ""
        for response in responses:
            if isinstance(response, Exception):
                self._logger.error(response)
                continue
            text_summary += f"\n{response}"

        template_kwargs = {
            "content": text_summary,
            "question": query,
        }
        prompt = self._configuration.prompt_strategy.build_prompt(**template_kwargs)

        model_response = await self.chat_with_model(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            completion_parser=self._parse_response,
        )
        return AbilityAction(
            ability_name=self.name(),
            ability_args={"query": query},
            success=True,
            message=model_response.content["content"],
        )

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

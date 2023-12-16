from typing import List
import logging
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.environment import Environment
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
    OpenAIProvider,
)
from superpilot.framework.tools.search_engine import SearchEngine, SearchEngineType
from superpilot.framework.tools.web_browser import WebBrowserEngine
from superpilot.framework.tools.summarizer import Summarizer
from superpilot.core.configuration import Config
from superpilot.core.planning.strategies import SummarizerStrategy
import asyncio


class SearchAndSummarizeAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.framework.abilities.search_summarise.SearchAndSummarizeAbility",
        ),
        language_model_required=LanguageModelConfiguration(
            model_name=OpenAIModelName.GPT3_16K,
            provider_name=ModelProviderName.OPENAI,
            temperature=0.9,
        )

    )

    def __init__(
        self,
            environment: Environment,
            configuration: AbilityConfiguration = default_configuration,
            prompt_strategy: SummarizerStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")
        self._language_model_provider = environment.get("model_providers").get(configuration.language_model_required.provider_name)
        self._search_engine = SearchEngine(config=self._env_config, engine=SearchEngineType.DIRECT_GOOGLE)

        if prompt_strategy is None:
            prompt_strategy = SummarizerStrategy(
                model_classification=SummarizerStrategy.default_configuration.model_classification,
                system_prompt=SummarizerStrategy.default_configuration.system_prompt,
                user_prompt_template=SummarizerStrategy.default_configuration.user_prompt_template,
            )
        self._prompt_strategy = prompt_strategy

    @classmethod
    def description(cls) -> str:
        return "Search and summarize information from the internet using search engines based on Playwright or Selenium Browser"

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
            },
            "system_text": {
                "type": "string",
                "description": "System text to define the requirements and format of the search and summarization.",
                "default": "SEARCH_AND_SUMMARIZE_SYSTEM",
            },
        }

    async def __call__(self, query: str, **kwargs) -> Context:
        no_google = (
            not self._env_config.google_api_key
            or "YOUR_API_KEY" == self._env_config.google_api_key
        )
        no_serpapi = (
            not self._env_config.serp_api_key
            or "YOUR_API_KEY" == self._env_config.serp_api_key
        )
        # print(self._env_config)
        # no_serper = not self._configuration.serper_api_key or 'YOUR_API_KEY' == self._configuration.serper_api_key

        if no_serpapi and no_google:
            self._logger.warning(
                "Configure one of SERPAPI_API_KEY, SERPER_API_KEY, GOOGLE_API_KEY to unlock full feature"
            )
            return None

        self._logger.debug(query)
        rsp = await self._search_engine.run(query)
        if not rsp:
            self._logger.error("empty rsp...")
            return Content.add_content_item("Empty Response", ContentType.TEXT)

        self._logger.info(rsp)

        print(rsp)
        # Scraping the links
        new_search_urls = [link["link"] for link in rsp if link]
        # Create a list to hold the coroutine objects
        tasks = [WebBrowserEngine().run(url) for url in new_search_urls]
        # Gather the results as they become available
        text_responses = await asyncio.gather(*tasks, return_exceptions=True)

        tasks = [
            Summarizer().run(response, query, new_search_urls[i])
            for i, response in enumerate(text_responses)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        text_summary = ""
        for response in responses:
            if response and not isinstance(response, Exception):
                text_summary += response + "\n\n"

        return Context([await self.get_content_item(text_summary, query, None)])

    async def get_content_item(self, content: str, query: str, url: str) -> Content:
        # template_kwargs = {
        #     "content": content,
        #     "question": query,
        # }
        # prompt = self._configuration.prompt_strategy.build_prompt(**template_kwargs)
        # model_response = await self.chat_with_model(
        #     model_prompt=prompt.messages,
        #     functions=prompt.functions,
        #     completion_parser=self._parse_response,
        # )
        # text_summary = model_response.content["content"]
        return Content.add_content_item(content, ContentType.TEXT, source=url)

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

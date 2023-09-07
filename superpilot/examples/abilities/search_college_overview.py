import logging
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.environment import Environment
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.framework.llm.base import ChatSequence
from superpilot.framework.llm.utils import create_chat_completion
from superpilot.framework.tools.search_engine import SearchEngine, SearchEngineType
from superpilot.framework.tools.web_browser import WebBrowserEngine
from superpilot.core.configuration import Config
from superpilot.core.planning.strategies import SummarizerStrategy
import asyncio


class SearchCollegeOverview(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.SearchCollegeOverview",
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
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")
        self._language_model_provider = environment.get("model_providers").get(
            configuration.language_model_required.provider_name
        )
        self._search_engine = SearchEngine(
            config=self._env_config, engine=SearchEngineType.DIRECT_GOOGLE
        )

        if prompt_strategy is None:
            prompt_strategy = SummarizerStrategy(
                model_classification=SummarizerStrategy.default_configuration.model_classification,
                system_prompt=SummarizerStrategy.default_configuration.system_prompt,
                user_prompt_template=SummarizerStrategy.default_configuration.user_prompt_template,
            )
        self._prompt_strategy = prompt_strategy

    @classmethod
    def description(cls) -> str:
        return "Search & Provide the college overview information from the internet using search engines based on Playwright or Selenium Browser"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "query": {
                "type": "string",
                "description": "Name of the College Name for which need the overview",
            },
            "context": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "Additional context to refine overview details.",
                },
                "description": "Contextual information to guide the summarization.",
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
        rsp = await self._search_engine.run(
            query, max_results=2, gl="in", siteSearch="https://www.careers360.com"
        )
        if not rsp:
            self._logger.error("empty rsp...")
            return Content.add_content_item("Empty Response", ContentType.TEXT)

        self._logger.info(rsp)

        new_search_urls = [link["link"] for link in rsp if link]
        # Create a list to hold the coroutine objects
        tasks = [WebBrowserEngine().run(url) for url in new_search_urls]
        # Gather the results as they become available
        text_responses = await asyncio.gather(*tasks, return_exceptions=True)

        tasks = [
            self.summarize_content(response, config=self._env_config)
            for i, response in enumerate(text_responses)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        text_summary = ""
        for response in responses:
            if response and not isinstance(response, Exception):
                text_summary += response + "\n\n"

        return Context([await self.get_content_item(text_summary, query, None)])

    async def get_content_item(self, content: str, query: str, url: str) -> Content:
        return Content.add_content_item(content, ContentType.TEXT, source=url)

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

    async def summarize_content(self, content, **kwargs):
        promt = """
        Use Below content, and generate an understandable summary of the content accordingly and segregate the info along with heading as per content.
        content :\n{content}
        Also remove all the unnecessary information from the content and provide the summary of the content.
        """
        system_message = """
                    You are a college content summarizer,
                    You can use the provided the college overview information from the internet using search engines based on Playwright or Selenium Browser and then convert into the readable summary along with the respective heading as per the content.
                    """
        config: Config = kwargs.get("config")
        summarization_prompt = ChatSequence.for_model(
            kwargs.get("model", config.fast_llm_model)
        )
        summarization_prompt.add("system", system_message)
        summarization_prompt.add("user", promt.format(content=content))
        try:
            response = create_chat_completion(
                prompt=summarization_prompt,
                temperature=0.9,
                **kwargs,
            )
            return response.content
        except Exception as e:
            print(f"Error summarizing content: {str(e)}")
            return None

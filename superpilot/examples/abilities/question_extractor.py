import json
import logging

from bs4 import BeautifulSoup
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.environment import Environment
from superpilot.core.context.schema import Content, ContentType
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.framework.tools.search_engine import SearchEngine, SearchEngineType
from superpilot.framework.tools.web_browser import WebBrowserEngine
from superpilot.core.configuration import Config
from superpilot.core.planning.strategies import SummarizerStrategy
from superpilot.framework.tools.web_browser.web_browser_engine_type import WebBrowserEngineType
from superpilot.core.planning.strategies.utils import json_loads


class QuestionExtractor(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.QuestionExtractor",
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
            config=self._env_config, engine=SearchEngineType.SERPAPI_GOOGLE
        )

    @classmethod
    def description(cls) -> str:
        return "Search & Extract the HTML Text using search engines based on Playwright or Selenium Browser"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "query": {
                "type": "string",
                "description": "Question to be asked",
            }
        }

    async def __call__(self, query: str, **kwargs):
        no_google = (
            not self._env_config.google_api_key
            or "YOUR_API_KEY" == self._env_config.google_api_key
        )
        no_serpapi = (
            not self._env_config.serp_api_key
            or "YOUR_API_KEY" == self._env_config.serp_api_key
        )

        if no_serpapi and no_google:
            self._logger.warning(
                "Configure one of SERPAPI_API_KEY, SERPER_API_KEY, GOOGLE_API_KEY to unlock full feature"
            )
            return None

        self._logger.debug(query)
        rsp = await self._search_engine.run(query, max_results=5)
        if not rsp:
            return None

        new_search_urls = [link for link in json_loads(rsp) if link]
        # print(new_search_urls)
        filter_link = None
        for link in new_search_urls:
            if 'chegg.com' in link['link']:
                print("page", link)
                filter_link = link['link']
                break
        if filter_link is None:
            return None
        data = None
        data = await WebBrowserEngine(
            parse_func=self.get_page_content, engine=WebBrowserEngineType.SELENIUM
        ).run(filter_link)
        return data

    async def get_content_item(self, content: str, query: str, url: str) -> Content:
        return Content.add_content_item(content, ContentType.TEXT, source=url)

    def get_page_content(self, page: str):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page, "html.parser")

        ele = soup.find("div", {"id": "question-transcript"})
        if ele:
            print("Found in question-transcript", ele)
            return ele
        print("Not Found in question-transcript")
        # desired_ids = ["question-transcript", "q-body"]
        # return soup.find_all("div", id=lambda x: x in desired_ids)
        desired_classes = ["styled__QuestionBody-sc-1f9k7g9-2", "question"]  # replace with your class names
        divs = soup.find_all("div", class_=lambda x: x in desired_classes)
        return "\n".join(i.text.strip() for i in divs)

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

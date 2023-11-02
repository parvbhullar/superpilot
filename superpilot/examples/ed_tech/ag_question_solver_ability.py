import json
import logging
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.environment import Environment
from superpilot.core.context.schema import Content, ContentType, Context
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.examples.abilities.utlis.scraperapi import scrape_page
from superpilot.framework.tools.search_engine import SearchEngine, SearchEngineType
# from superpilot.framework.tools.web_browser import WebBrowserEngine
from superpilot.core.configuration import Config
from superpilot.core.planning.strategies import SummarizerStrategy
# from superpilot.framework.tools.web_browser.web_browser_engine_type import (
#     WebBrowserEngineType,
# )
from superpilot.core.planning.strategies.utils import json_loads


class AGQuestionSolverAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.AGQuestionSolverAbility",
        ),
        language_model_required=LanguageModelConfiguration(
            model_name=OpenAIModelName.GPT4,
            provider_name=ModelProviderName.OPENAI,
            temperature=0.1,
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

    @classmethod
    def description(cls) -> str:
        return "Solve any question(Math, Physics, Chemistry) using gpt4 agents"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "query": {
                "type": "string",
                "description": "Question to be asked",
            }
        }

    async def __call__(self, query: str, **kwargs):
        self._logger.debug(query)
        context = Context()
        context.add(self.get_content(query, **kwargs))
        return context

    def get_content(self, query: str, **kwargs) -> Content:
        import autogen
        config_list = autogen.config_list_from_json(
            "superpilot/tests/OAI_CONFIG_LIST",
            filter_dict={
                "model": {
                    "gpt-4",
                    "gpt4",
                    "gpt-4-32k",
                    "gpt-4-32k-0314",
                    "gpt-4-32k-v0314",
                }
            }
        )

        openai_key = self._env_config.openai_api_key
        config_list = [
            {'model': 'gpt-4', 'api_key': openai_key},
            {'model': 'gpt-4-32k', 'api_key': openai_key}
        ]

        from autogen.agentchat.contrib.math_user_proxy_agent import MathUserProxyAgent

        autogen.ChatCompletion.start_logging()

        # 1. create an AssistantAgent instance named "assistant"
        assistant = autogen.AssistantAgent(
            name="assistant",
            system_message="You are a helpful assistant.",
            llm_config={
                "request_timeout": 600,
                "seed": 42,
                "config_list": config_list,
            }
        )

        # 2. create the MathUserProxyAgent instance named "mathproxyagent"
        # By default, the human_input_mode is "NEVER", which means the agent will not ask for human input.
        mathproxyagent = MathUserProxyAgent(
            name="mathproxyagent",
            human_input_mode="NEVER",
            code_execution_config={"use_docker": False},
        )

        mathproxyagent.initiate_chat(assistant, problem=query, prompt_type="python")
        # print("*" * 32, "Chatting", "*" * 32)

        return Content.add_content_item(self.format_messages(mathproxyagent.chat_messages), ContentType.TEXT)

    def format_messages(self, messages):
        messages = list(messages.values())[0]
        # Skip the first message and extract the 'content' from the rest
        contents = [msg['role'] + " : " + msg['content'] for msg in messages[1:]]
        # Join the contents with a space to form the prompt
        prompt = '\n\n'.join(contents)
        return prompt

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

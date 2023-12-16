import logging
import os
from time import sleep
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.environment import Environment
from superpilot.core.context.schema import Content, ContentType, Context
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.core.configuration import Config
from superpilot.core.planning.strategies import SummarizerStrategy
from pydantic import BaseModel, Extra, root_validator
from typing import Any, Callable, Dict, List, Optional, Union


class WolframAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.WolframAbility",
        ),
        language_model_required=LanguageModelConfiguration(
            model_name=OpenAIModelName.GPT4,
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
        output, is_success = self.execute_one_wolfram_query(query)
        print("Executing Ability Query: ", query, output, is_success)
        openai_key = self._env_config.openai_api_key

        # print("*" * 32, "Chatting", "*" * 32)

        return Content.add_content_item(
            self.format_messages([output]), ContentType.TEXT
        )

    def format_messages(self, messages):
        messages = list(messages.values())[0]
        # Skip the first message and extract the 'content' from the rest
        contents = [msg["role"] + " : " + msg["content"] for msg in messages[1:]]
        # Join the contents with a space to form the prompt
        prompt = "\n\n".join(contents)
        return prompt

    def execute_one_wolfram_query(self, query: str):
        """Run one wolfram query and return the output.

        Args:
            query: string of the query.

        Returns:
            output: string with the output of the query.
            is_success: boolean indicating whether the query was successful.
        """
        # wolfram query handler
        wolfram = WolframAlphaAPIWrapper()
        output, is_success = wolfram.run(query)
        if output == "":
            output = "Error: The wolfram query is invalid."
            is_success = False
        return output, is_success

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}


def get_from_dict_or_env(data: Dict[str, Any], key: str, env_key: str, default: Optional[str] = None) -> str:
    """Get a value from a dictionary or an environment variable."""
    if key in data and data[key]:
        return data[key]
    elif env_key in os.environ and os.environ[env_key]:
        return os.environ[env_key]
    elif default is not None:
        return default
    else:
        raise ValueError(
            f"Did not find {key}, please add an environment variable"
            f" `{env_key}` which contains it, or pass"
            f"  `{key}` as a named parameter."
        )


class WolframAlphaAPIWrapper(BaseModel):
    """Wrapper for Wolfram Alpha.

    Docs for using:

    1. Go to wolfram alpha and sign up for a developer account
    2. Create an app and get your APP ID
    3. Save your APP ID into WOLFRAM_ALPHA_APPID env variable
    4. pip install wolframalpha

    """

    wolfram_client: Any  #: :meta private:
    wolfram_alpha_appid: Optional[str] = None

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator(skip_on_failure=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        wolfram_alpha_appid = get_from_dict_or_env(values, "wolfram_alpha_appid", "WOLFRAM_ALPHA_APPID")
        values["wolfram_alpha_appid"] = wolfram_alpha_appid

        try:
            import wolframalpha

        except ImportError:
            raise ImportError("wolframalpha is not installed. " "Please install it with `pip install wolframalpha`")
        client = wolframalpha.Client(wolfram_alpha_appid)
        values["wolfram_client"] = client

        return values

    def run(self, query: str) -> str:
        """Run query through WolframAlpha and parse result."""
        from urllib.error import HTTPError

        is_success = False  # added
        res = None
        for _ in range(20):
            try:
                res = self.wolfram_client.query(query)
                break
            except HTTPError:
                sleep(1)
            except Exception:
                return (
                    "Wolfram Alpha wasn't able to answer it. Please try a new query for wolfram or use python.",
                    is_success,
                )
        if res is None:
            return (
                "Wolfram Alpha wasn't able to answer it (may due to web error), you can try again or use python.",
                is_success,
            )

        try:
            print("WF"*32, res)
            if not res["@success"]:
                return (
                    "Your Wolfram query is invalid. Please try a new query for wolfram or use python.",
                    is_success,
                )
            assumption = next(res.pods).text
            answer = ""
            for result in res["pod"]:
                if result["@title"] == "Solution":
                    answer = result["subpod"]["plaintext"]
                if result["@title"] == "Results" or result["@title"] == "Solutions":
                    for i, sub in enumerate(result["subpod"]):
                        answer += f"ans {i}: " + sub["plaintext"] + "\n"
                    break
            if answer == "":
                answer = next(res.results).text

        except Exception:
            return (
                "Wolfram Alpha wasn't able to answer it. Please try a new query for wolfram or use python.",
                is_success,
            )

        if answer is None or answer == "":
            # We don't want to return the assumption alone if answer is empty
            return "No good Wolfram Alpha Result was found", is_success
        is_success = True
        return f"Assumption: {assumption} \nAnswer: {answer}", is_success

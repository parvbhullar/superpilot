import logging
import os
import time
import inflection
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.context.schema import Context, FileContentItem
from superpilot.core.environment import Environment
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.planning.strategies.markdown import MarkdownGeneratorStrategy
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.core.configuration import Config


class GenerateMarkdownContent(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.GenerateMarkdownContent",
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
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")
        self._language_model_provider = environment.get("model_providers").get(
            configuration.language_model_required.provider_name
        )
        self._prompt_strategy = MarkdownGeneratorStrategy()
        self._workspace = environment.get("workspace")

    @classmethod
    def description(cls) -> str:
        return "Generate Markdown Content from Provided content"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "content": {
                "type": "string",
                "description": "content to generate markdown from",
            }
        }

    async def __call__(self, context: str, **kwargs):
        prompt = self._prompt_strategy.build_prompt(context)
        print(prompt)
        model_response = await self._language_model_provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            completion_parser=self._parse_response,
            model_name=self._configuration.language_model_required.model_name,
        )
        text_summary = model_response.content["content"]
        work_space_media = f"{self._workspace.root}/media"
        os.makedirs(work_space_media, exist_ok=True)
        task = kwargs.get("task")
        if task:
            objective = task.objective
            objective = " ".join(objective.split(" ")[:10])[:30]
            file_path = f"{work_space_media}/{inflection.underscore(objective).replace(' ','-')}.md"
        else:
            file_path = f"{work_space_media}/summary{int(time.time())}.md"
        with open(file_path, "w") as f:
            f.write(text_summary)
        content = FileContentItem(file_path=file_path)
        return Context(items=[content])

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

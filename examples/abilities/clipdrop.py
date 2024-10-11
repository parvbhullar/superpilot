import logging
import os
import time
import inflection
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.context.schema import Context, ImageContentItem
from superpilot.core.environment import Environment
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.core.configuration import Config
from superpilot.examples.abilities.utlis.clipdrop import generate_image_with_clip_drop


class ClipDropGenerator(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.ClipDropGenerator",
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
        self._workspace = environment.get("workspace")
        self._language_model_provider = environment.get("model_providers").get(
            configuration.language_model_required.provider_name
        )

    @classmethod
    def description(cls) -> str:
        return "Generate Image from the Provide query"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "query": {
                "type": "string",
                "description": "Query for which we need to generate the image",
            }
        }

    async def __call__(self, query, **kwargs):
        request_body = {"prompt": (None, query, "text/plain")}
        print(request_body)
        headers = {"x-api-key": f"{self._env_config.clipdrop_api_key}"}
        response, status = generate_image_with_clip_drop(request_body, headers)
        if not status:
            raise Exception(response)
        work_space_media = f"{self._workspace.root}/media/clipdrop"
        os.makedirs(work_space_media, exist_ok=True)
        items = []
        task = kwargs.get("task")
        if task:
            objective = task.objective
            objective = " ".join(objective.split(" ")[:10])[:30]
            file_path = f"{work_space_media}/{inflection.underscore(objective).replace(' ','-')}_{int(time.time())}.png"
        else:
            file_path = f"{work_space_media}/image_{int(time.time())}.png"
        with open(file_path, "wb") as f:
            f.write(response)
        content = ImageContentItem(file_path=file_path)
        items.append(content)
        return Context(items=items)

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

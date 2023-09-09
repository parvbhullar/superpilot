import base64
import logging
import os
import time
from typing import List
import inflection
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.context.schema import Context, FileContentItem
from superpilot.core.environment import Environment
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.core.configuration import Config
from superpilot.examples.abilities.schema.stable_diffusion import (
    ArtStylePreset,
    TextPrompts,
)
from superpilot.examples.abilities.utlis.stable_diffusion import generate_image_with_sd


class StableDiffusionGenerator(Ability):
    DEFAULT_BODY = {
        "steps": 40,
        "width": 1024,
        "height": 1024,
        "seed": 0,
        "cfg_scale": 5,
        "samples": 1,
    }

    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.StableDiffusionGenerator",
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

    @classmethod
    def description(cls) -> str:
        return "Generate Image from the Provide Text Prompts & sytle"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "text_prompts": {
                "type": "list",
                "description": "List of Text Prompts",
            },
            "style_preset": {
                "type": "string",
                "description": "Style Preset",
            },
        }

    def generate_body(
        self, text_prompts: List[TextPrompts], style_preset: ArtStylePreset, **kwargs
    ) -> dict:
        default_request_body = self.DEFAULT_BODY
        default_request_body["text_prompts"] = text_prompts
        default_request_body["style_preset"] = style_preset.value
        default_request_body.update(kwargs)
        return default_request_body

    async def __call__(
        self, text_prompts: List[TextPrompts], style_preset: ArtStylePreset, **kwargs
    ):
        request_body = self.generate_body(text_prompts, style_preset, **kwargs)
        headers = {"Authorization": f"Bearer {self._env_config.stability_api_key}"}
        response, status = generate_image_with_sd(request_body, headers)
        if not status:
            raise Exception(response)
        work_space_media = f"{self._workspace.root}/media"
        os.makedirs(work_space_media, exist_ok=True)
        items = []
        task = kwargs.get("task")
        for i, image in enumerate(response["artifacts"]):
            if task:
                objective = task.objective
                file_path = f"{work_space_media}/{inflection.underscore(objective).replace(' ','-')}_{i}.jpg"
            else:
                file_path = f"{work_space_media}/image_{i}_{int(time.time())}.jpg"
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(image["base64"]))
            content = FileContentItem(file_path=file_path)
            items.append(content)
        return Context(items=items)

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

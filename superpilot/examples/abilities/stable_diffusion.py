import base64
import logging
import os
import time
from typing import List
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
from superpilot.examples.abilities.schema.stable_diffusion import (
    ArtStylePreset,
    TextPrompts,
)
from superpilot.examples.abilities.utlis.stable_diffusion import generate_image_with_sd
from superpilot.examples.prompt_generator.stabledifusion_prompt import (
    StableDiffusionPrompt,
)


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
        self._language_model_provider = environment.get("model_providers").get(
            configuration.language_model_required.provider_name
        )
        self._prompt_strategy = StableDiffusionPrompt.factory()

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

    def generate_body(
        self,
        text_prompts: List[TextPrompts],
        style_preset: ArtStylePreset = ArtStylePreset.FANTASY_ART,
        **kwargs,
    ) -> dict:
        default_request_body = self.DEFAULT_BODY
        default_request_body["text_prompts"] = text_prompts
        default_request_body["style_preset"] = style_preset
        if style_preset == "none":
            default_request_body["style_preset"] = ArtStylePreset.FANTASY_ART.value
        kwargs.pop("height", None)
        kwargs.pop("width", None)
        kwargs.pop("cfg_scale", None)
        kwargs.pop("clip_guidance_preset", None)
        kwargs.pop("sampler", None)
        default_request_body.update(kwargs)
        return default_request_body

    async def __call__(self, query, **kwargs):
        # query = self._prompt_strategy.text_generate(query)
        # print(query)
        prompt = self._prompt_strategy.build_prompt(query)
        model_response = await self._language_model_provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            completion_parser=self._prompt_strategy.parse_response_content,
            model_name=self._configuration.language_model_required.model_name,
        )
        sd_prompt = model_response.content
        request_body = self.generate_body(**sd_prompt)
        print(request_body)
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
                objective = " ".join(objective.split(" ")[:10])[:30]
                file_path = f"{work_space_media}/{inflection.underscore(objective).replace(' ','-')}_{i}_{int(time.time())}.jpg"
            else:
                file_path = f"{work_space_media}/image_{i}_{int(time.time())}.jpg"
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(image["base64"]))
            content = ImageContentItem(file_path=file_path)
            items.append(content)
        return Context(items=items)

    @staticmethod
    def _parse_response(response_content: dict) -> dict:
        return {"content": response_content["content"]}

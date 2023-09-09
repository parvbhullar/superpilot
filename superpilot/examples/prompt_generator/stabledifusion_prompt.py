import json

from superpilot.core.configuration import SystemConfiguration, UserConfigurable
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelPrompt,
)
from superpilot.core.planning.strategies.utils import json_loads
from superpilot.core.resource.model_providers import (
    LanguageModelFunction,
    LanguageModelMessage,
    MessageRole,
    SchemaModel,
)
from superpilot.core.planning.settings import PromptStrategyConfiguration
from pydantic import Field
from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field, conint, confloat
from typing import List, Optional
from enum import Enum


class TextPrompt(BaseModel):
    text: str = Field(..., max_length=2000, description="The prompt itself")
    weight: float = Field(..., description="Weight of the prompt (use negative numbers for negative prompts)")


class ClipGuidancePreset(str, Enum):
    FAST_BLUE = "FAST_BLUE"
    FAST_GREEN = "FAST_GREEN"
    NONE = "NONE"
    SIMPLE = "SIMPLE"
    SLOW = "SLOW"
    SLOWER = "SLOWER"
    SLOWEST = "SLOWEST"


class Sampler(str, Enum):
    DDIM = "DDIM"
    DDPM = "DDPM"
    K_DPMPP_2M = "K_DPMPP_2M"
    K_DPMPP_2S_ANCESTRAL = "K_DPMPP_2S_ANCESTRAL"
    K_DPM_2 = "K_DPM_2"
    K_DPM_2_ANCESTRAL = "K_DPM_2_ANCESTRAL"
    K_EULER = "K_EULER"
    K_EULER_ANCESTRAL = "K_EULER_ANCESTRAL"
    K_HEUN = "K_HEUN"
    K_LMS = "K_LMS"

class StylePreset(str, Enum):
    _3D_MODEL = "3d-model"
    ANALOG_FILM = "analog-film"
    ANIME = "anime"
    CINEMATIC = "cinematic"
    COMIC_BOOK = "comic-book"
    DIGITAL_ART = "digital-art"
    ENHANCE = "enhance"
    FANTASY_ART = "fantasy-art"
    ISOMETRIC = "isometric"
    LINE_ART = "line-art"
    LOW_POLY = "low-poly"
    MODELING_COMPOUND = "modeling-compound"
    NEON_PUNK = "neon-punk"
    ORIGAMI = "origami"
    PHOTOGRAPHIC = "photographic"
    PIXEL_ART = "pixel-art"
    TILE_TEXTURE = "tile-texture"

class StableDiffusionPromptModel(SchemaModel):
    """
    This class serves as a data model for Stable Diffusion Prompts used in AI art generation.
    It includes various fields that describe the properties and attributes of the art piece to be generated.
    Each field is self-explanatory and maps directly to a specific aspect of the art piece.
    """
    height: conint(multiple_of=64, ge=128) = Field(512, description="Height of the image in pixels. Must be in increments of 64.")
    width: conint(multiple_of=64, ge=128) = Field(512, description="Width of the image in pixels. Must be in increments of 64.")
    text_prompts: List[TextPrompt] = Field(..., description="An array of text prompts to use for generation.")
    cfg_scale: conint(ge=0, le=35) = Field(7, description="How strictly the diffusion process adheres to the prompt text")
    clip_guidance_preset: ClipGuidancePreset = Field(ClipGuidancePreset.NONE, description="Which clip guidance preset to use")
    sampler: Optional[Sampler] = Field(None, description="Which sampler to use for the diffusion process.")
    samples: conint(ge=1, le=10) = Field(1, description="Number of images to generate")
    seed: conint(ge=0, le=4294967295) = Field(0, description="Random noise seed")
    steps: conint(ge=10, le=150) = Field(50, description="Number of diffusion steps to run")
    style_preset: Optional[StylePreset] = Field(None, description="Pass in a style preset to guide the image model towards a particular style.")
    extras: Optional[dict] = Field(None, description="Extra parameters passed to the engine for experimental features.")

    class Config:
        schema_extra = {
            "example": {
                "height": 512,
                "width": 512,
                "text_prompts": [{"text": "A lighthouse on a cliff", "weight": 0.5}],
                "cfg_scale": 7,
                "clip_guidance_preset": "NONE",
                "sampler": "DDIM",
                "samples": 1,
                "seed": 0,
                "steps": 50,
                "style_preset": "3d-model",
                "extras": {}
            }
        }


class StableDiffusionPrompt(SimplePrompt):
    DEFAULT_SYSTEM_PROMPT = (
        """
        As a prompt generator for a generative AI called "StableDiffusion", you will create image prompts for the AI to visualize. I will give you a concept, and you will provide a detailed prompt for StableDiffusion AI to generate an image.
        Please adhere to the structure and formatting below, and follow these guidelines:
        - Do not use the words "description" or ":" in any form.
        - Write each prompt in one line without using return.
        """
    )

    DEFAULT_USER_PROMPT_TEMPLATE = (
        """
        {task_objective}
        use above information to learn about Stable diffusion Prompting, and use it to create prompts.
        Stable Diffusion is an AI art generation model similar to DALLE-2. 
        It can be used to create impressive artwork by using positive and negative prompts. Positive prompts describe what should be included in the image. 
        very important is that the Positive Prompts are usually created in a specific structure: 
        Negative Prompts describe what should not be included in the image.
        Quality: High definition, 4K, 8K, 64K
        use this Negative Prompts and add some words what you think that match to Prompt: 2 heads, 2 faces, cropped image, out of frame, draft, deformed hands, signatures, twisted fingers, double image, long neck, malformed hands, nwltiple heads, extra limb, ugty, poorty drawn hands, missing limb, disfigured, cut-off, ugty, grain, Iow-res, Deforrned, blurry, bad anaWny, disfigured, poorty drawn face, mutation, mutated, floating limbs, disconnected limbs, long body, disgusting, poorty drawn, mutilated, mangled, surreal, extra fingers, duplicate artifacts, morbid, gross proportions, missing arms, mutated hands, mutilated hands, cloned face, malformed,ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, bad anatomy, watermark, signature, cut off, low contrast, underexposed, overexposed, bad art, beginner, amateur, distorted face, blurry, draft, grainy, etc 
        very important: use an artist matching to the art style , or dont write any artist if it is realistic style or some of that.
        Important Rules:
        - don't use any pronouns
        - avoid using these words: in a, the, with, of, the, an, and, is, by, of.
        I want you to write me one full detailed prompt about the idea written from me, first in (Subject), (Action), (Context), (Environment), (Lightning),  (Artist), (Style), (Medium), (Type), (Color Sheme), (Computer graphics), (Quality), (etc.). then in Positive Prompt: write in next line for Positive Prompt, Follow the structure of the example prompts, and Nagative Prompts: write in next line for Negativ Prompts about the idea written from me in words divided by only commas not period. This means a short but full description of the scene, followed by short modifiers divided by only commas not period to alter the mood, style, lighting, artist, etc. write all prompts in english.
        """
    )

    DEFAULT_PARSER_SCHEMA = StableDiffusionPromptModel.function_schema()

    default_configuration = PromptStrategyConfiguration(
        model_classification=LanguageModelClassification.SMART_MODEL,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
        parser_schema=DEFAULT_PARSER_SCHEMA,
    )

    def __init__(
            self,
            model_classification: LanguageModelClassification = default_configuration.model_classification,
            system_prompt: str = default_configuration.system_prompt,
            user_prompt_template: str = default_configuration.user_prompt_template,
            parser_schema: Dict = None,
    ):
        super().__init__(
            model_classification=model_classification,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            parser_schema=parser_schema,
        )

    @classmethod
    def factory(cls, system_prompt=None, user_prompt_template=None, parser=None, model_classification=None)\
            -> "StableDiffusionPrompt":
        config = cls.default_configuration.dict()
        if model_classification:
            config['model_classification'] = model_classification
        if system_prompt:
            config['system_prompt'] = system_prompt
        if user_prompt_template:
            config['user_prompt_template'] = user_prompt_template
        if parser:
            config['parser_schema'] = parser
        return cls(**config)

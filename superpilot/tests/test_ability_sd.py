import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.core.configuration.config import get_config

from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.tests.test_env_simple import get_env
from superpilot.examples.abilities.stable_diffusion import StableDiffusionGenerator
from superpilot.examples.abilities.schema.stable_diffusion import ArtStylePreset

import asyncio

model_providers = ModelProviderFactory.load_providers()
config = get_config()
env = get_env({})


ability = StableDiffusionGenerator(environment=env, configuration=config)

extra = {
    "height": 512,
    "width": 512,
    # "cfg_scale": 7,
    # "clip_guidance_preset": "FAST_BLUE",
    "sampler": "DDIM",
    "samples": 1,
    "seed": 0,
    "steps": 50,
}
text_prompts = [
    {
        "text": "Romantic painting of a ship sailing in a stormy sea, with dramatic lighting and powerful waves",
        "weight": 1,
    }
]
result = asyncio.run(
    ability(text_prompts, style_preset=ArtStylePreset.PHOTOGRAPHIC, **extra)
)

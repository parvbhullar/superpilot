import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.core.configuration.config import get_config

from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.tests.test_env_simple import get_env
from superpilot.examples.abilities.stable_diffusion import StableDiffusionGenerator

# from superpilot.examples.abilities.schema.stable_diffusion import ArtStylePreset
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.examples.pilots.tasks.overview import CollegeOverViewTaskPilot

from superpilot.core.planning.schema import Task
from superpilot.core.context.schema import Context
import asyncio

model_providers = ModelProviderFactory.load_providers()
config = get_config()
env = get_env({})


# ability = StableDiffusionGenerator(environment=env, configuration=config)

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
text_prompts = [
    {
        "text": "4k anime girl in a kimono and purple clothing, in the style of photo-realistic drawings, light white and light gray, qian xuan, exaggerated nobility, sabattier filter, kawacy, accurate and detailed --ar 18:25 --s 750 --niji 5",
        "weight": 1.7,
    }
]
# result = asyncio.run(
#     ability(text_prompts, style_preset=ArtStylePreset.FANTASY_ART, **extra)
# )

logger = logging.getLogger("SearchAndSummarizeAbility")
context = Context()
print("************************************************************")

ALLOWED_ABILITY = {
    StableDiffusionGenerator.name(): StableDiffusionGenerator.default_configuration
}
super_ability_registry = SuperAbilityRegistry.factory(env, ALLOWED_ABILITY)

overview_task_pilot = CollegeOverViewTaskPilot(super_ability_registry, model_providers)
task = Task.factory(
    "portrait of ana de armas eating pizza, intricate, elegant, glowing lights, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration, art by wlop, mars ravelo, and greg rutkowski"
)
context = asyncio.run(overview_task_pilot.execute(task, context))
print(context.format_numbered())

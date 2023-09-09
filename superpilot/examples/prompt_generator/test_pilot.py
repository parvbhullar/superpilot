import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import logging
from superpilot.framework.abilities import (
    TextSummarizeAbility,
)
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIProvider,
    OpenAIModelName,
    ModelProviderFactory
)
from superpilot.core.context.schema import Context
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.pilot.task.super import SuperTaskPilot
from superpilot.core.pilot.task.simple import SimpleTaskPilot


ALLOWED_ABILITY = {
    # SearchAndSummarizeAbility.name(): SearchAndSummarizeAbility.default_configuration,
    TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
}
from superpilot.tests.test_env_simple import get_env
from superpilot.core.pilot import SuperPilot
from superpilot.core.configuration import get_config
from superpilot.core.resource.model_providers.schema import ModelProviderCredentials
from superpilot.core.planning.base import PromptStrategy 
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.examples.prompt_generator.midjourney_prompt import MidjourneyPrompt
from superpilot.examples.prompt_generator.stabledifusion_prompt import StableDiffusionPrompt

# Flow executor -> Context
#
# Context -> Search & Summarise [WebSearch, KnowledgeBase, News] - parrallel] -> Context
# Context -> Analysis[FinancialAnalysis] -> Context
# Context -> Write[TextStream, PDF, Word] -> Context
# Context -> Respond[Twitter, Email, Stream]] -> Context
# Context -> Finalise[PDF, Word] -> Context


async def test_pilot():

    # Ask for few sample images of the person to be created
    # Generate few prompts from the LLMs to generate the images from midjourney
    # Ask for the final image to be created from the LLMs
    # Return the images to the user.

    # query = "How to file the GSTR1"
    query = "Logo for UNPOD an ai startup"

    # context = Context()

    config = get_config()

    # print(config.openai_api_key)
    # Load Model Providers
    model_providers = ModelProviderFactory.load_providers()
    super_prompt = MidjourneyPrompt.factory()
    super_prompt = StableDiffusionPrompt.factory()

    prompt_pilot = SimpleTaskPilot.factory(prompt_strategy=super_prompt.get_config(), model_providers=model_providers)

    print("***************** Executing SimplePilot ******************************\n")
    response = await prompt_pilot.execute(query)
    print(response)


if __name__ == "__main__":
    asyncio.run(test_pilot())

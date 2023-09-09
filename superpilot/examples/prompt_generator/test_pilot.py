import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from superpilot.framework.abilities import (
    TextSummarizeAbility,
)
from superpilot.core.resource.model_providers import ModelProviderFactory
from superpilot.core.pilot.task.simple import SimpleTaskPilot


ALLOWED_ABILITY = {
    # SearchAndSummarizeAbility.name(): SearchAndSummarizeAbility.default_configuration,
    TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
}
from superpilot.examples.prompt_generator.midjourney_prompt import MidjourneyPrompt

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

    model_providers = ModelProviderFactory.load_providers()
    super_prompt = MidjourneyPrompt.factory()

    midjourney_pilot = SimpleTaskPilot.factory(
        prompt_strategy=super_prompt.get_config(), model_providers=model_providers
    )

    print("***************** Executing SimplePilot ******************************\n")
    response = await midjourney_pilot.execute(query)
    print(response)


if __name__ == "__main__":
    asyncio.run(test_pilot())

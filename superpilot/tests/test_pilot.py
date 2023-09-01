import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from superpilot.framework.abilities import (
    TextSummarizeAbility,
)
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIProvider,
)
from superpilot.core.context.schema import Context
from superpilot.core.ability.super import SuperAbilityRegistry


ALLOWED_ABILITY = {
    # SearchAndSummarizeAbility.name(): SearchAndSummarizeAbility.default_configuration,
    TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
}
from superpilot.tests.test_env_simple import get_env
from superpilot.core.pilot import SuperPilot
from superpilot.core.configuration import get_config
from superpilot.core.resource.model_providers.schema import ModelProviderCredentials

# Flow executor -> Context
#
# Context -> Search & Summarise [WebSearch, KnowledgeBase, News] - parrallel] -> Context
# Context -> Analysis[FinancialAnalysis] -> Context
# Context -> Write[TextStream, PDF, Word] -> Context
# Context -> Respond[Twitter, Email, Stream]] -> Context
# Context -> Finalise[PDF, Word] -> Context


async def test_pilot():
    # query = "How to file the GSTR1"
    query = "What is the weather in Mumbai"

    logger = logging.getLogger("SearchAndSummarizeAbility")
    context = Context()

    config = get_config()

    # Load Model Providers
    open_ai_provider = OpenAIProvider.create_provider(config.openai_api_key)
    model_providers = {ModelProviderName.OPENAI: open_ai_provider}

    # Load Prompt Strategy


    # Load Abilities



    ability_settings = SuperAbilityRegistry.default_settings
    # ability_settings.configuration.config = config
    ability_settings.configuration.abilities = {
        ability_name: ability for ability_name, ability in ALLOWED_ABILITY.items()
    }

    env = get_env({})

    super_ability_registry = SuperAbilityRegistry(
        ability_settings,
        environment=env,
    )

    planner = env.get("planning")
    # ability_registry = env.get("ability_registry")

    # user_configuration = {}
    # pilot_settings = SuperPilot.compile_settings(client_logger, user_configuration)

    # Step 2. Provision the environment.
    # environment_workspace = SuperPilot.provision_environment(environment_settings, client_logger)

    user_objectives = "What is the weather in Mumbai"
    # SuperPilot.default_settings.configuration
    pilot_settings = SuperPilot.default_settings
    pilot = SuperPilot(pilot_settings, super_ability_registry, planner, env)
    print(await pilot.initialize(user_objectives))
    print("***************** Pilot Initiated - Planing Started ******************************\n")
    print(await pilot.plan())
    print("***************** Pilot Initiated - Planing Completed ******************************\n")
    while True:
        print("***************** Pilot Started - Exec Started ******************************\n")
        # current_task, next_ability = await pilot.determine_next_ability(plan)
        # print(parse_next_ability(current_task, next_ability))
        # user_input = click.prompt(
        #     "Should the pilot proceed with this ability?",
        #     default="y",
        # )
        # if not next_ability["next_ability"]:
        #     print("Agent is done!", "No Next Ability Found")
        #     break
        # ability_result = await pilot.execute_next_ability(user_input)
        # print(parse_ability_result(ability_result))
        break


if __name__ == "__main__":
    asyncio.run(test_pilot())

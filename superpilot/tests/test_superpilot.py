import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from superpilot.framework.abilities import (
    TextSummarizeAbility,
)
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIProvider,
    AnthropicApiProvider,
    AnthropicModelName,
    OllamaModelName,
    OllamaApiProvider,
)
from superpilot.core.context.schema import Context
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.examples.ed_tech.ag_question_solver_ability import AGQuestionSolverAbility
from superpilot.examples.pilots.tasks.super import SuperTaskPilot
from superpilot.core.planning.schema import Task

ALLOWED_ABILITY = {
    # SearchAndSummarizeAbility.name(): SearchAndSummarizeAbility.default_configuration,
    # TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
    AGQuestionSolverAbility.name(): AGQuestionSolverAbility.default_configuration,
}
from superpilot.tests.test_env_simple import get_env
from superpilot.core.pilot import SuperPilot
from superpilot.core.configuration import get_config
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
)

# Flow executor -> Context
#
# Context -> Search & Summarise [WebSearch, KnowledgeBase, News] - parrallel] -> Context
# Context -> Analysis[FinancialAnalysis] -> Context
# Context -> Write[TextStream, PDF, Word] -> Context
# Context -> Respond[Twitter, Email, Stream]] -> Context
# Context -> Finalise[PDF, Word] -> Context


async def test_pilot():
    query = "File GSTR1 using the GSTN Portal"

    context = Context()

    config = get_config()

    env = get_env({})

    super_ability_registry = SuperAbilityRegistry.factory(env, ALLOWED_ABILITY)
    planner = env.get("planning")
    ability_registry = env.get("ability_registry")

    user_objectives = query
    # SuperPilot.default_settings.configuration
    pilot_settings = SuperPilot.default_settings
    pilot = SuperPilot(pilot_settings, super_ability_registry, planner, env)
    print(await pilot.initialize(user_objectives))
    print(
        "***************** Pilot Initiated - Planing Started ******************************\n"
    )
    print(await pilot.plan())
    print(
        "***************** Pilot Initiated - Planing Completed ******************************\n"
    )
    while True:
        print(
            "***************** Pilot Started - Exec Started ******************************\n"
        )
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

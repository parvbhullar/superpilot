import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import logging
from superpilot.core.flow.simple import SuperTaskPilot
from superpilot.core.configuration.config import get_config
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

# Flow executor -> Context
#
# Context -> Search & Summarise [WebSearch, KnowledgeBase, News] - parrallel] -> Context
# Context -> Analysis[FinancialAnalysis] -> Context
# Context -> Write[TextStream, PDF, Word] -> Context
# Context -> Respond[Twitter, Email, Stream]] -> Context
# Context -> Finalise[PDF, Word] -> Context

if __name__ == "__main__":
    # query = "How to file the GSTR1"
    query = "What is the weather in Mumbai"

    logger = logging.getLogger("SearchAndSummarizeAbility")
    context = Context()

    model_providers = {ModelProviderName.OPENAI: OpenAIProvider()}
    config = get_config()
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

    planner = env.get("planner")
    ability_registry = env.get("ability_registry")


    search_step = SuperTaskPilot(super_ability_registry, model_providers)
    # search_step.run(query, context)
    # flow = SimpleFlow(query)
    # flow_res = asyncio.run(
    #     flow.run(ability_schema=super_ability_registry.dump_abilities())
    # )
    print("\n\n")
    print("***************** Flow Result ******************************\n")
    # print(flow_res.dict())
    print("\n***************** Flow End ******************************")
    # if flow_res and flow_res.steps:
    #     for step in flow_res.steps:
    #         objective = step.ability.arguments.pop("query", None)
    #         if not objective:
    #             continue
    #         task = Task(
    #             objective=objective,
    #             priority=1,
    #             type="text",
    #             ready_criteria=[],
    #             acceptance_criteria=[],
    #         )
    #         kargs = {
    #             "query": objective,
    #             "task_context": task.context,
    #             **step.ability.arguments,
    #         }
    #         context = asyncio.run(search_step.execute(task, context, **kargs))
    # task = Task(
    #     objective=query,
    #     priority=1,
    #     type="text",
    #     ready_criteria=[],
    #     acceptance_criteria=[],
    # )
    # kargs = {"query": task.objective, "task_context": task.context}
    # context = asyncio.run(search_step.execute(task, context, **kargs))

    # summarise_step = SimpleStep(ALLOWED_ABILITY, {ModelProviderName.OPENAI: OpenAIProvider()})
    # # context = asyncio.run(search_step.execute(task, context, **kargs))
    #
    # flow = List[search_step, summarise_step]

    # flow = Flow(steps=[search_step, summarise_step], strategy="prompt")
    # asyncio.run(flow.execute(**kargs))
    print("\n\n\n\n")
    print("************************************************************")
    print(context.format_numbered())

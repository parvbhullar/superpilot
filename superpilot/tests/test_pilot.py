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
    # query = "How to file the GSTR1"
    query = "What is the weather in Mumbai"
    query = """
    1. Step 1: State the Null Hypothesis. ...
    2. Step 2: State the Alternative Hypothesis....
    3. Step 3: Set. ...
    4. Step 4: Collect Data. ...
    5. Step 5: Calculate a test statistic....
    (o) Show Transcribed Text
    For each test below, submit your answers to steps mathbf1 through mathbf5 of the significance testing process. In steos 4 and 5 , explain why you chose that answer.
    3. Test if the population mean years of education (EDUC) is more than 12. Submit your answers to steps mathbf1 through mathbf5 of the significance testing process.
    One-sample mathrmt test
     begintabular|c|c|c|c|c|c|c|
     hline Variable     Obs     Mean     Std. Err.     Std. Dev.     [95 
     hline educ     2,345     13.73177     .0614208     2.974313     13.61133     13.85221   
     hline  multicolumn4|c| mean = mean ( educ )             =28.1952   
     hline  multicolumn4|c| Ho: mean =12     degrees     of freedom =     =2344   
     hline
     endtabular
    
    Ha: mean <12
    operatornamePr( mathrmT< mathrmt)=1.0000
    Ha: mean !=12
    operatornamePr(| mathrmT|>| mathrmt|)=0.0000
    Ha: mean > 12
    operatornamePr( mathrmT> mathrmt)=0.0000

    """

    query = """
    In the complex numbers, where i^2=-1, which of the following is equal to the result of squaring the expression (i + 4)
        a. 4i
        b. 16i
        c. 15 + 8i
        d. i + 16
        e. 17-18i
    """

    context = Context()

    config = get_config()

    print(config.openai_api_key)
    # Load Model Providers
    open_ai_provider = OpenAIProvider.factory(config.openai_api_key)
    anthropic_provider = AnthropicApiProvider.factory(config.anthropic_api_key)
    ollama_provider = OllamaApiProvider.factory(config.anthropic_api_key)
    model_providers = {ModelProviderName.OPENAI: open_ai_provider, ModelProviderName.ANTHROPIC: anthropic_provider}
    # model_providers = {ModelProviderName.OLLAMA: ollama_provider}

    # Load Prompt Strategy
    SimpleTaskPilot.default_configuration.models = {
        LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
            model_name=AnthropicModelName.CLAUD_2_INSTANT,
            provider_name=ModelProviderName.ANTHROPIC,
            temperature=1,
        ),
        LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
            model_name=AnthropicModelName.CLAUD_2,
            provider_name=ModelProviderName.ANTHROPIC,
            temperature=0.9,
        ),
    }
    # SimpleTaskPilot.default_configuration.models = {
    #     LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
    #         model_name=OllamaModelName.LLAMA2,
    #         provider_name=ModelProviderName.OLLAMA,
    #         temperature=1,
    #     ),
    #     LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
    #         model_name=OllamaModelName.WIZARD_MATH,
    #         provider_name=ModelProviderName.OLLAMA,
    #         temperature=0.9,
    #     ),
    # }

    # task_pilot = SimpleTaskPilot(model_providers=model_providers)

    # print("***************** Executing SimplePilot ******************************\n")
    # response = await task_pilot.execute(query, context)
    # print(response)
    # print("***************** Executing SimplePilot Completed ******************************\n")

    # exit(0)
    # # Load Prompt Strategy
    # super_prompt = SimplePrompt.factory()
    # # Load Abilities
    # prompt = super_prompt.build_prompt(query)
    # print(prompt)
    env = get_env({})

    super_ability_registry = SuperAbilityRegistry.factory(env, ALLOWED_ABILITY)
    pilot = SuperTaskPilot(super_ability_registry, model_providers)
    task = Task.factory(query)
    context = await pilot.execute(task, context)
    print(context)
    exit(0)
    #
    super_ability_registry = SuperAbilityRegistry.factory(env, ALLOWED_ABILITY)
    #
    # search_step = SuperTaskPilot(super_ability_registry, model_providers)

    planner = env.get("planning")
    ability_registry = env.get("ability_registry")

    # user_configuration = {}
    # pilot_settings = SuperPilot.compile_settings(client_logger, user_configuration)

    # Step 2. Provision the environment.
    # environment_workspace = SuperPilot.provision_environment(environment_settings, client_logger)



    exit(0)
    user_objectives = "What is the weather in Mumbai"
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

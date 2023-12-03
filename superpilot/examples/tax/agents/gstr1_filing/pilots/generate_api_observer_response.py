import os
import sys

from superpilot.core.pilot.task.settings import TaskPilotConfiguration
from superpilot.core.planning.schema import ExecutionNature, LanguageModelClassification
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from superpilot.framework.abilities import (
    TextSummarizeAbility,
)
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIProvider,
    OpenAIModelName,
)
from superpilot.core.context.schema import Context
from superpilot.core.pilot.task.simple import SimpleTaskPilot


ALLOWED_ABILITY = {
    # SearchAndSummarizeAbility.name(): SearchAndSummarizeAbility.default_configuration,
    TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
}
from superpilot.core.configuration import get_config
from superpilot.core.planning.strategies.simple import SimplePrompt

async def test_pilot(response):
    # query = "How to file the GSTR1"
    query = f""" Analyse the reponse and give errors in crisp and human readable format, also let user know that we 
    are uploading the success count documents: {response}
    """

    context = Context()

    config = get_config()

    print(config.openai_api_key)
    # builder = ModelProviderFactory()
    # model_providers = builder.load_providers()
    # Load Model Providers
    open_ai_provider = OpenAIProvider.factory(config.openai_api_key)
    model_providers = {ModelProviderName.OPENAI: open_ai_provider}

    task_pilot = SimpleTaskPilot(
        model_providers=model_providers,
        configuration=TaskPilotConfiguration(
            location=PluginLocation(
                storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                storage_route="superpilot.core.flow.simple.SuperTaskPilot",
            ),
            execution_nature=ExecutionNature.SIMPLE,
            prompt_strategy=SimplePrompt.default_configuration,
            models={
                LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                    model_name=OpenAIModelName.GPT4_TURBO,
                    provider_name=ModelProviderName.OPENAI,
                    temperature=1,
                ),
                LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                    model_name=OpenAIModelName.GPT4,
                    provider_name=ModelProviderName.OPENAI,
                    temperature=0.9,
                ),
            },
        )
    )

    print("***************** Executing SimplePilot ******************************\n")
    response = await task_pilot.execute(query, context)
    print(response)
    print(
        "***************** Executing SimplePilot Completed ******************************\n"
    )
    return response

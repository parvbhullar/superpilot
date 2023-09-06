import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import logging
from superpilot.core.configuration.config import get_config
from superpilot.framework.abilities import (
    TextSummarizeAbility,
)
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIProvider,
)
from superpilot.core.context.schema import Context
from superpilot.examples.pilots.tasks.overview import CollegeOverViewTaskPilot
from superpilot.core.ability.super import SuperAbilityRegistry


ALLOWED_ABILITY = {
    TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
}
from superpilot.tests.test_env_simple import get_env


if __name__ == "__main__":
    query = "What is the weather in Mumbai"

    logger = logging.getLogger("SearchAndSummarizeAbility")
    context = Context()

    model_providers = {ModelProviderName.OPENAI: OpenAIProvider()}
    config = get_config()

    env = get_env({})
    print("************************************************************")
    super_ability_registry = SuperAbilityRegistry.factory(env, ALLOWED_ABILITY)

    overview_task_pilot = CollegeOverViewTaskPilot(
        super_ability_registry, model_providers
    )
    print(context.format_numbered())

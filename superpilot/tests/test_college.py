# flake8: noqa

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import logging
from superpilot.core.configuration.config import get_config
from superpilot.framework.abilities import (
    TextSummarizeAbility,
)

from superpilot.examples.abilities.search_college_overview import SearchCollegeOverview
from superpilot.examples.abilities.generate_md import GenerateMarkdownContent
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIProvider,
)
from superpilot.core.planning.schema import Task
from superpilot.core.context.schema import Context
from superpilot.examples.pilots.tasks.overview import CollegeOverViewTaskPilot
from superpilot.core.ability.super import SuperAbilityRegistry


ALLOWED_ABILITY = {
    SearchCollegeOverview.name(): SearchCollegeOverview.default_configuration,
    GenerateMarkdownContent.name(): GenerateMarkdownContent.default_configuration,
    # TextSummarizeAbility.name(): TextSummarizeAbility.default_configuration,
}
from superpilot.tests.test_env_simple import get_env
import asyncio


if __name__ == "__main__":
    query = "Raj Kumar Goel Institute Of Technology"

    logger = logging.getLogger("SearchAndSummarizeAbility")
    context = Context()
    config = get_config()
    model_providers = {
        ModelProviderName.OPENAI: OpenAIProvider.factory(api_key=config.openai_api_key)
    }

    env = get_env({})
    print("************************************************************")
    super_ability_registry = SuperAbilityRegistry.factory(env, ALLOWED_ABILITY)

    overview_task_pilot = CollegeOverViewTaskPilot(
        super_ability_registry, model_providers
    )
    task = Task.factory(query)
    context = asyncio.run(overview_task_pilot.execute(task, context))
    print(context.format_numbered())

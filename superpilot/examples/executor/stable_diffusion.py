from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.configuration.config import get_config

from superpilot.core.context.schema import Context
from superpilot.core.planning.schema import Task
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.abilities.stable_diffusion import StableDiffusionGenerator
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.pilots.tasks.super import SuperTaskPilot
from superpilot.tests.test_env_simple import get_env

ALLOWED_ABILITY = {
    StableDiffusionGenerator.name(): StableDiffusionGenerator.default_configuration
}


class StableDiffusionImageExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    config = get_config()
    env = get_env({})
    context = Context()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        super_ability_registry = SuperAbilityRegistry.factory(self.env, ALLOWED_ABILITY)
        self.pilot = SuperTaskPilot(super_ability_registry, self.model_providers)

    async def run(self, query):
        task = Task.factory(query)
        context = await self.pilot.execute(task, self.context)
        return context

from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.configuration.config import get_config

from superpilot.core.context.schema import Context
from superpilot.core.planning.schema import Task
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.abilities.question_extractor import QuestionExtractor
from superpilot.examples.executor.base import BaseExecutor
from superpilot.examples.pilots.tasks.super import SuperTaskPilot
from superpilot.tests.test_env_simple import get_env

ALLOWED_ABILITY = {
    QuestionExtractor.name(): QuestionExtractor.default_configuration
}


class QuestionExtractoreExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    config = get_config()
    env = get_env({})
    context = Context()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.ability = QuestionExtractor(environment=self.env)


    async def run(self, query):
        context = await self.ability(query)
        return context

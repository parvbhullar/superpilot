from typing import List
from superpilot.core.pilot.task.model import ModelTaskPilot
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.resource.model_providers.factory import AI_MODELS
from superpilot.core.resource.model_providers.schema import (
    LanguageModelMessage,
    ModelProviderName,
)
from superpilot.examples.executor.base import BaseExecutor


class ModelPilotExecutor(BaseExecutor):
    def __init__(
        self, provider_name: ModelProviderName, model_name: AI_MODELS, **kwargs
    ):
        for key, value in kwargs.items():
            setattr(self, key, value)
        model_provider = self.prepare_model_provider(provider_name, model_name)
        self.pilot = ModelTaskPilot.factory(model_provider=model_provider)

    @classmethod
    def prepare_model_provider(cls, provider_name, model_name):
        return LanguageModelConfiguration(
            model_name=model_name,
            provider_name=provider_name,
            temperature=0.8,
        )

    async def run(
        self,
        query,
        message_history: List[LanguageModelMessage] = [],
    ):
        response = await self.pilot.execute(query, message_history)
        return response

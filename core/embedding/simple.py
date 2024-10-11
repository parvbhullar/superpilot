import logging
from typing import Dict

from superpilot.core.configuration import Configurable
from superpilot.core.embedding.base import EmbeddingModel, EmbeddingModelResponse
from superpilot.core.embedding.settings import (
    EmbeddingModelConfiguration,
    EmbeddingModelSettings,
)
from superpilot.core.resource.model_providers import (
    EmbeddingModelProvider,
    ModelProviderName,
    OpenAIModelName,
)


class SimpleEmbeddingModel(EmbeddingModel, Configurable):
    default_settings = EmbeddingModelSettings(
        name="simple_embedding_model",
        description="A simple embedding model.",
        configuration=EmbeddingModelConfiguration(
            model_name=OpenAIModelName.ADA,
            provider_name=ModelProviderName.OPENAI,
        ),
    )

    def __init__(
        self,
        settings: EmbeddingModelSettings,
        logger: logging.Logger,
        model_providers: Dict[ModelProviderName, EmbeddingModelProvider],
    ):
        self._configuration = settings.configuration
        self._logger = logger
        self._model_provider = model_providers[self._configuration.provider_name]

    async def get_embedding(self, text: str) -> EmbeddingModelResponse:
        """Get the embedding for a prompt.

        Args:
            text: The text to embed.

        Returns:
            The response from the embedding model.

        """
        response = await self._model_provider.create_embedding(
            text,
            model_name="embedding_model",
            embedding_parser=lambda x: x,
        )
        return EmbeddingModelResponse.model_validate(response.dict())

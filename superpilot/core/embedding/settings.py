from superpilot.core.configuration import (
    SystemConfiguration,
    SystemSettings,
    UserConfigurable,
)
from superpilot.core.resource.model_providers import ModelProviderName


class EmbeddingModelConfiguration(SystemConfiguration):
    """Configuration for the embedding model"""

    model_name: str = UserConfigurable()
    provider_name: ModelProviderName = UserConfigurable()


class EmbeddingModelSettings(SystemSettings):
    configuration: EmbeddingModelConfiguration

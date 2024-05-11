from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers.schema import (
    ModelProviderDetail,
    ModelProviderName,
)


MODEL_PROVIDERS_DICT = {
    ModelProviderName.OPENAI: ModelProviderDetail(
        name=ModelProviderName.OPENAI,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.resource.model_providers.OpenAIProvider",
        ),
    ),
    ModelProviderName.ANTHROPIC: ModelProviderDetail(
        name=ModelProviderName.HUGGINGFACE,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.resource.model_providers.AnthropicApiProvider",
        ),
    ),
    ModelProviderName.OLLAMA: ModelProviderDetail(
        name=ModelProviderName.OLLAMA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.resource.model_providers.OllamaApiProvider",
        ),
    ),
    ModelProviderName.DEEPINFRA: ModelProviderDetail(
        name=ModelProviderName.DEEPINFRA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.resource.model_providers.DeepInfraProvider",
        ),
    ),
    ModelProviderName.TOGETHER: ModelProviderDetail(
        name=ModelProviderName.DEEPINFRA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="superpilot.core.resource.model_providers.TogetherAIProvider",
        ),
    ),
}

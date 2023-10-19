import logging
from typing import Dict
from superpilot.core.plugin.simple import (
    PluginLocation,
    PluginStorageFormat,
    SimplePluginService,
)
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    LanguageModelProvider,
)
from superpilot.core.configuration import SystemConfiguration, SystemSettings


class ModelProviderConfiguration(SystemConfiguration):
    user_configuration: Dict = dict()
    location: PluginLocation


class ProviderFactorySettings(SystemSettings):
    models: Dict[str, ModelProviderConfiguration]


class ModelProviderFactory:
    default_settings = ProviderFactorySettings(
        name="simple_model_provider_factory",
        description="A simple model provider factory.",
        models={
            ModelProviderName.OPENAI: ModelProviderConfiguration(
                user_configuration={},
                location=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="superpilot.core.resource.model_providers.OpenAIProvider",
                ),
            ),
            ModelProviderName.ANTHROPIC: ModelProviderConfiguration(
                user_configuration={},
                location=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="superpilot.core.resource.model_providers.AnthropicApiProvider",
                ),
            ),
        },
    )

    def __init__(
        self,
        settings: ProviderFactorySettings,
        logger: logging.Logger,
        model_providers: Dict[ModelProviderName, LanguageModelProvider] = None,
    ):
        self._settings = settings
        self._logger = logger
        self._model_providers = model_providers

    @classmethod
    def factory(
        cls,
        model_provider_configs: Dict[
            ModelProviderName, ModelProviderConfiguration
        ] = None,
        logger: logging.Logger = None,
    ):
        if logger is None:
            logger = logging.getLogger(cls.__name__)
        model_providers = cls.load_providers(
            model_provider_configs=model_provider_configs,
            logger=logger,
        )
        return cls(
            settings=cls.default_settings,
            logger=logger,
            model_providers=model_providers,
        )

    @classmethod
    def load_providers(
        cls,
        model_provider_configs: Dict[
            ModelProviderName, ModelProviderConfiguration
        ] = None,
        logger: logging.Logger = None,
    ):
        if logger is None:
            logger = logging.getLogger(cls.__name__)

        if model_provider_configs is not None:
            cls.default_settings.models.update(model_provider_configs)

        model_providers = {}
        for model_provider_name, config in cls.default_settings.models.items():
            model_providers.update(
                {
                    model_provider_name: cls._get_model_provider_instance(
                        config.user_configuration,
                        config.location,
                        logger,
                    )
                }
            )

        return model_providers

    @classmethod
    def _get_model_provider_instance(
        cls,
        user_configuration: dict,
        location: PluginLocation,
        logger: logging.Logger,
        *args,
        **kwargs,
    ):
        model_provider_class = SimplePluginService.get_plugin(location)
        model_provider_settings = model_provider_class.init_settings(
            **user_configuration
        )
        model_provider_parameter = model_provider_class.__init__.__annotations__
        model_provider_kwargs = {}
        for key in kwargs:
            if key in model_provider_parameter:
                model_provider_kwargs[key] = kwargs[key]
        if "logger" in model_provider_parameter:
            model_provider_kwargs["logger"] = logger.getChild(
                model_provider_class.__name__
            )
        model_provider_instance = model_provider_class(
            model_provider_settings,
            *args,
            **model_provider_kwargs,
        )
        return model_provider_instance


# Usage example
if __name__ == "__main__":
    model_provider_list = ModelProviderFactory.load_providers()
    print(model_provider_list)

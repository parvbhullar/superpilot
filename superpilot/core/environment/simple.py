import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from superpilot.core.ability import (
    SimpleAbilityRegistry,
)
from superpilot.core.environment.base import Environment
from superpilot.core.environment.settings import (
    EnvConfiguration,
    EnvSystems,
    EnvSystemSettings,
    EnvSettings,
)
from superpilot.core.configuration import Configurable, ConfigBuilder
from superpilot.core.memory import SimpleMemory
from superpilot.core.planning import SimplePlanner, Task, TaskStatus
from superpilot.core.plugin.simple import (
    PluginLocation,
    PluginStorageFormat,
    SimplePluginService,
)
from superpilot.core.workspace.simple import SimpleWorkspace
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
    OpenAIProvider,
)


class SimpleEnv(Environment, Configurable):
    default_settings = EnvSystemSettings(
        name="simple_environment",
        description="A simple environment.",
        configuration=EnvConfiguration(
            request_id="",
            creation_time="",
            systems=EnvSystems(
                ability_registry=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="superpilot.core.ability.SimpleAbilityRegistry",
                ),
                memory=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="superpilot.core.memory.SimpleMemory",
                ),
                openai_provider=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="superpilot.core.resource.model_providers.OpenAIProvider",
                ),
                planning=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="superpilot.core.planning.SimplePlanner",
                ),
                workspace=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="superpilot.core.workspace.SimpleWorkspace",
                )
            ),
        ),
    )

    def __init__(
        self,
        settings: EnvSystemSettings,
        logger: logging.Logger,
        # ability_registry: SimpleAbilityRegistry,
        memory: SimpleMemory,
        openai_provider: OpenAIProvider,
        planning: SimplePlanner,
        workspace: SimpleWorkspace,
    ):
        self.configuration = settings.configuration
        self.env_config = ConfigBuilder.build_config_from_env()
        self.logger = logger
        # self.ability_registry = ability_registry
        self.memory = memory
        # FIXME: Need some work to make this work as a dict of providers
        #  Getting the construction of the config to work is a bit tricky
        self.openai_provider = openai_provider
        self.model_providers = {ModelProviderName.OPENAI: openai_provider}  # TODO load models from model registry
        self.planning = planning
        self.workspace = workspace

    @classmethod
    def from_workspace(
        cls,
        workspace_path: Path,
        logger: logging.Logger,
    ) -> "SimpleEnv":
        environment_settings = SimpleWorkspace.load_environment_settings(workspace_path, cls.name())
        environment_args = {}

        environment_args["settings"] = environment_settings.environment
        environment_args["logger"] = logger

        environment_args["workspace"] = cls._get_system_instance(
            "workspace",
            environment_settings,
            logger,
        )
        environment_args["openai_provider"] = cls._get_system_instance(
            "openai_provider",
            environment_settings,
            logger,
        )
        environment_args["planning"] = cls._get_system_instance(
            "planning",
            environment_settings,
            logger,
            model_providers={"openai": environment_args["openai_provider"]},
        )
        environment_args["memory"] = cls._get_system_instance(
            "memory",
            environment_settings,
            logger,
            workspace=environment_args["workspace"],
        )

        # environment_args["ability_registry"] = cls._get_system_instance(
        #     "ability_registry",
        #     environment_settings,
        #     logger,
        #     workspace=environment_args["workspace"],
        #     memory=environment_args["memory"],
        #     model_providers={"openai": environment_args["openai_provider"]},
        # )

        return cls(**environment_args)

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    ################################################################
    # Factory interface for environment bootstrapping and initialization #
    ################################################################

    @classmethod
    def factory(cls, user_configuration: dict, logger: logging.Logger) -> "SimpleEnv":

        logger.debug("Getting environment settings")

        environment_workspace = (
            user_configuration.get("workspace", {}).get("configuration", {}).get("root", "")
        )

        # Configure logging before we do anything else.
        # logger.set_level(logging.DEBUG if debug else logging.INFO)

        # working_directory = Path(__file__).parent.parent.parent

        # Load the configuration from the environment.
        # config = ConfigBuilder.load_env(workdir=working_directory)
        # user_configuration['config'] = config

        if not environment_workspace:  # We don't have an environment yet.
            #################
            # Bootstrapping #
            #################
            # Step 1. Collate the user's settings with the default system settings.
            environment_settings: EnvSettings = cls.compile_settings(
                logger,
                user_configuration,
            )

            # Step 2. Provision the environment.
            environment_workspace = cls.provision_environment(
                environment_settings, logger
            )
            print("environment is provisioned")

        # launch environment interaction loop
        environment = cls.from_workspace(
            environment_workspace,
            logger,
        )
        print("environment is loaded")
        # print(environment._configuration)
        return environment

    @classmethod
    def build_user_configuration(cls) -> dict[str, Any]:
        """Build the user's configuration."""
        configuration_dict = {
            "environment": cls.get_user_config(),
        }

        system_locations = configuration_dict["environment"]["configuration"]["systems"]
        for system_name, system_location in system_locations.items():
            system_class = SimplePluginService.get_plugin(system_location)
            configuration_dict[system_name] = system_class.get_user_config()
        configuration_dict = _prune_empty_dicts(configuration_dict)
        return configuration_dict

    @classmethod
    def compile_settings(
        cls, logger: logging.Logger, user_configuration: dict
    ) -> EnvSettings:
        """Compile the user's configuration with the defaults."""
        logger.debug("Processing environment system configuration.")
        configuration_dict = {
            "environment": cls.build_configuration(
                user_configuration.get("environment", {})
            ).dict(),
        }

        system_locations = configuration_dict["environment"]["configuration"]["systems"]

        # Build up default configuration
        system_parameters = cls.__init__.__annotations__
        for system_name, system_location in system_locations.items():
            logger.debug(f"Compiling configuration for system {system_name}")
            if system_name not in system_parameters:
                logger.debug(f"System {system_name} not found in Base Model class.")
                continue
            system_class = SimplePluginService.get_plugin(system_location)
            configuration_dict[system_name] = system_class.build_configuration(
                user_configuration.get(system_name, {})
            ).dict()

        return EnvSettings.parse_obj(configuration_dict)

    @classmethod
    def provision_environment(
        cls,
        environment_settings: EnvSettings,
        logger: logging.Logger,
    ):
        environment_settings.environment.configuration.creation_time = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        workspace: SimpleWorkspace = cls._get_system_instance(
            "workspace",
            environment_settings,
            logger=logger,
        )
        return workspace.setup_workspace(environment_settings, logger, cls.name())

    def get(self, system_name: str, *args, **kwargs) -> Any:
        try:
            system_instance = getattr(self, system_name)
        except AttributeError as e:
            self.logger.error(f"System {system_name} not found in environment.")
            return None
        return system_instance

    @classmethod
    def _get_system_instance(
        cls,
        system_name: str,
        environment_settings: EnvSettings,
        logger: logging.Logger,
        *args,
        **kwargs,
    ):
        system_locations = environment_settings.environment.configuration.systems.dict()
        system_settings = getattr(environment_settings, system_name)
        system_class = SimplePluginService.get_plugin(system_locations[system_name])
        system_parameter = system_class.__init__.__annotations__
        system_kwargs = {}
        for key in kwargs:
            if key in system_parameter:
                system_kwargs[key] = kwargs[key]
        if 'logger' in system_parameter:
            system_kwargs['logger'] = logger.getChild(system_name)
        system_instance = system_class(
            system_settings,
            *args,
            **system_kwargs,
        )
        return system_instance


def _prune_empty_dicts(d: dict) -> dict:
    """
    Prune branches from a nested dictionary if the branch only contains empty dictionaries at the leaves.

    Args:
        d: The dictionary to prune.

    Returns:
        The pruned dictionary.
    """
    pruned = {}
    for key, value in d.items():
        if isinstance(value, dict):
            pruned_value = _prune_empty_dicts(value)
            if (
                pruned_value
            ):  # if the pruned dictionary is not empty, add it to the result
                pruned[key] = pruned_value
        else:
            pruned[key] = value
    return pruned

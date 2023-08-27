import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import click
from pathlib import Path
from superpilot.core.environment import EnvSettings, SimpleEnv
from superpilot.core.runner.client_lib.logging import get_client_logger
from superpilot.framework.config import ConfigBuilder, check_openai_api_key
import asyncio


def get_env(user_configuration: dict):
    """Run the Superpilot CLI client."""

    client_logger = get_client_logger()
    client_logger.debug("Getting environment settings")

    environment_workspace = (
        user_configuration.get("workspace", {}).get("configuration", {}).get("root", "")
    )

    # Configure logging before we do anything else.
    # client_logger.set_level(logging.DEBUG if debug else logging.INFO)
    working_directory = Path(
        __file__
    ).parent.parent.parent

    # Load the configuration from the environment.
    config = ConfigBuilder.load_env(workdir=working_directory)
    # user_configuration['config'] = config

    if not environment_workspace:  # We don't have an environment yet.
        #################
        # Bootstrapping #
        #################
        # Step 1. Collate the user's settings with the default system settings.
        environment_settings: EnvSettings = SimpleEnv.compile_settings(
            client_logger,
            user_configuration,
        )

        # Step 2. Provision the environment.
        environment_workspace = SimpleEnv.provision_environment(environment_settings, client_logger)
        print("environment is provisioned")

    # launch environment interaction loop
    environment = SimpleEnv.from_workspace(
        environment_workspace,
        client_logger,
    )
    print("environment is loaded")
    # print(environment._configuration)
    return environment

if __name__ == "__main__":
    get_env({})
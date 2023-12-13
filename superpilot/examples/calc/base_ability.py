from dataclasses import dataclass
from typing import List
import logging

from superpilot.core.ability import AbilityAction
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.configuration import Config
from superpilot.core.environment import Environment
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.planning import PromptStrategy
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat


class DefaultAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.DefaultAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
            self,
            environment: Environment,
            configuration: AbilityConfiguration = default_configuration,
            prompt_strategy: PromptStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def description(cls) -> str:
        return "default to call, summarises the task completion"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "task_summary": {
                "type": "string",
                "description": "verbose completion summary of the task"
            }
        }

    async def __call__(self, task_summary: str, **kwargs) -> Context:
        return Context.factory().add_content(task_summary)


class AddAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.AddAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
            self,
            environment: Environment,
            configuration: AbilityConfiguration = default_configuration,
            prompt_strategy: PromptStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def description(cls) -> str:
        return "Add two numbers."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "num1": {"type": "number", "description": "The first number."},
            "num2": {"type": "number", "description": "The second number."},
        }

    async def __call__(self, num1: float, num2: float, **kwargs) -> Context:
        callback = kwargs.get("callback")
        result = num1 + num2
        message = f"The sum is {result}."
        if callback:
            await callback.on_info(message)
        print(message)
        return Context.factory().add_content(message)


@dataclass
class MultiplyAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.MultiplyAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
            self,
            environment: Environment,
            configuration: AbilityConfiguration = default_configuration,
            prompt_strategy: PromptStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def description(cls) -> str:
        return "Multiply two numbers."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "num1": {"type": "number", "description": "The first number."},
            "num2": {"type": "number", "description": "The second number."},
        }

    async def __call__(self, num1: float, num2: float, **kwargs) -> Context:
        result = num1 * num2
        message = f"The Multiplication is {result}."
        print(message)
        # Rest of the method remains the same
        print(Context.factory().add_content(message))
        return Context.factory().add_content(message)


@dataclass
class SubtractAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.SubtractAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
            self,
            environment: Environment,
            configuration: AbilityConfiguration = default_configuration,
            prompt_strategy: PromptStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def description(cls) -> str:
        return "Subtract two numbers."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "num1": {"type": "number", "description": "The first number."},
            "num2": {"type": "number", "description": "The second number."},
        }

    async def __call__(self, num1: float, num2: float, **kwargs) -> Context:
        result = num1 - num2
        message = f"The difference is {result}."
        # Rest of the method remains the same
        return Context.factory().add_content(message)


@dataclass
class DivisionAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.DivisionAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
            self,
            environment: Environment,
            configuration: AbilityConfiguration = default_configuration,
            prompt_strategy: PromptStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def description(cls) -> str:
        return "Divide two numbers."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "num1": {"type": "number", "description": "The first number."},
            "num2": {"type": "number", "description": "The second number."},
        }

    async def __call__(self, num1: float, num2: float, **kwargs) -> Context:
        if num2 == 0:
            message = "Division by zero error."
            return Context.factory().add_content(message)
        result = num1 / num2
        message = f"The quotient is {result}."
        # Rest of the method remains the same
        return Context.factory().add_content(message)


@dataclass
class RootAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.RootAbility",
        ),
        packages_required=[],
        workspace_required=False,
    )

    def __init__(
            self,
            environment: Environment,
            configuration: AbilityConfiguration = default_configuration,
            prompt_strategy: PromptStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def description(cls) -> str:
        return "Calculate the root of a number."

    @classmethod
    def arguments(cls) -> dict:
        return {
            "num": {"type": "number", "description": "The first number."},
            "root": {"type": "number", "description": "The second number."},
        }

    async def __call__(self, num: float, root: float) -> Context:
        if root <= 0:
            message="Root must be greater than zero."
            return Context.factory().add_content(message)
        result = num ** (1 / root)
        message = f"The {root}-root of {num} is {result}."
        # Rest of the method remains the same
        return Context.factory().add_content(message)

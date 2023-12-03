import json
import logging

from pydantic import Field
from superpilot.core.ability import Ability
from superpilot.core.ability.base import AbilityConfiguration
from superpilot.core.configuration import Config
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.environment import Environment
from superpilot.core.planning.strategies import SummarizerStrategy
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import SchemaModel

from services.gstgptservice.agents.gstr1_filing.pilots.generate_api_observer_response import test_pilot


class ObserverResponseSchema(SchemaModel):
    """
    Schema for the API response.
    """
    question: str = Field(
        ..., description="relevant question to be asked to user"
    )
    info: str = Field(
        ..., description="relevant information to be given to user"
    )
    call_function: bool = Field(
        ..., description="please set it true if you think based on current context we can call function"
    )
    is_exit: bool = Field(
        ..., description="set is_exit true if you think user wants to exit"
    )
    # is_error: bool = Field(
    #     ..., description="set is_error true if you think there is any extact error and no question"
    # )

    @classmethod
    def name(cls) -> str:
        return "observer_response"


class ObserverAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.ObserverAbility",
        )
    )

    def __init__(
        self,
        environment: Environment,
        configuration: AbilityConfiguration = default_configuration,
        prompt_strategy: SummarizerStrategy = None,
    ):
        self._logger: logging.Logger = environment.get("logger")
        self._configuration = configuration
        self._env_config: Config = environment.get("env_config")

    @classmethod
    def name(cls) -> str:
        return "ObserverAbility"

    @classmethod
    def description(cls) -> str:
        return "Observe latest info in given context and communicate next steps to user"

    @classmethod
    def arguments(cls) -> dict:
        return ObserverResponseSchema.function_schema(arguments_format=True)

    async def __call__(self, ObserverResponseSchema: dict, **kwargs) -> Context:
        return Context([await self.get_content_item(json.dumps(ObserverResponseSchema))])

    async def get_content_item(self, content: str) -> Content:
        return Content.add_content_item(content, ContentType.DICT)

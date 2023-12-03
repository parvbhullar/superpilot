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


class ResMessage(SchemaModel):
    msg: str = Field(..., description="The message returned by the API call.")
    error: str = Field(..., description="The error returned by the API call.")


class ApiResponseSchema(SchemaModel):
    """
    Schema for the API response.
    """
    success: bool = Field(
        ..., description="Whether the API call was successful or not."
    )
    data: dict = Field(..., description="The data returned by the API call.")
    message: ResMessage = Field(..., description="The message returned by the API call.")

    @classmethod
    def name(cls) -> str:
        return "api_response"


class ApiResponseObserverAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.ApiResponseObserverAbility",
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
        return "ApiResponseObserverAbility"

    @classmethod
    def description(cls) -> str:
        return "Observe api_response given in context and communicate next steps to user"

    @classmethod
    def arguments(cls) -> dict:
        return ApiResponseSchema.function_schema(arguments_format=True)

    async def __call__(self, api_response: dict, **kwargs) -> Context:
        print(api_response)
        response = await test_pilot(api_response)
        print(response)
        return Context([await self.get_content_item(str(api_response))])

    async def get_content_item(self, content: str) -> Content:
        return Content.add_content_item(content, ContentType.DICT)

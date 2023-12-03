import logging
from typing import List

import requests
from pydantic import Field
from superpilot.core.ability import Ability
from superpilot.core.ability.base import AbilityConfiguration
from superpilot.core.configuration import Config
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.environment import Environment
from superpilot.core.planning.strategies import SummarizerStrategy
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import SchemaModel

from services.gstgptservice.agents.gstr1_filing.abilities.gstr1_data_transform_ability import ARAP_BASE_URL
from services.gstgptservice.agents.gstr1_filing.abilities.sale_data_import_ability import HeaderSchema
from services.gstgptservice.agents.gstr1_filing.gstr1_data_transformer_prompt import Document


class Gstr1SummaryAbilityArguments(SchemaModel):
    """
    Headers for the API call.
    """
    header: HeaderSchema = Field(
        ..., description="Header information for the API call"
    )


class GSRT1SummaryAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.GSRT1SummaryAbility",
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
    def description(cls) -> str:
        return "Provide summary of sales imported data, that will be used for uploading to goverment portal"

    @classmethod
    def arguments(cls) -> dict:
        args = Gstr1SummaryAbilityArguments.function_schema(arguments_format=True)
        print("Arguments GSRT1 Summary", args)
        return args

    async def __call__(self, Gstr1SummaryAbilityArguments: dict={}, **kwargs) -> Context:
        url = f"{ARAP_BASE_URL}/api/v1/saas-apis/invoice-summary/?screen_key=compare_data"
        header = Gstr1SummaryAbilityArguments["header"]
        response = requests.request("GET", url, headers=header)
        print(response.text)
        text = "Invoice Summary response:" + response.text
        return Context([await self.get_content_item(text, header, None)])

    async def get_content_item(self, content: str, header: dict, url: None) -> Content:
        return Content.add_content_item(
            content, ContentType.DICT, source=url, content_metadata={"header": header}
        )

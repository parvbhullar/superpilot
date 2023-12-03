import json
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
from services.gstgptservice.agents.gstr1_filing.gstr1_data_transformer_prompt import Document


class HeaderSchema(SchemaModel):
    gstin: str = Field(..., description="GSTIN (Goods and Services Tax Identification Number).")
    month: str = Field(..., description="Month in MM format.")
    year: str = Field(..., description="Year or year range in YYYY-YY format.")
    invoice: str = Field(..., description="Indicator for invoice ('Y' or 'N').")
    summary: str = Field(..., description="Indicator for summary ('Y' or 'N').")
    MiplApiKey: str = Field(..., description="API Key for MIPL (Mandatory Invoice Parameters List).")
    Content_Type: str = Field(..., description="Content type.", alias="Content-Type")


class ImportAbilityArguments(SchemaModel):
    """
    Container class representing a tree of questions to ask a question answer system.
    and its dependencies. Make sure every question is in the tree, and every question is asked only once.
    """

    json_data: List[Document] = Field(
        ..., description="List of gstr documents/rows to be processed"
    )
    header: HeaderSchema = Field(
        ..., description="Header information for the API call"
    )


class SalesDataImportAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.SalesDataImportAbility",
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
        return "Call the Sales Data Import API to import the sales data into the system"

    @classmethod
    def arguments(cls) -> dict:
        args = ImportAbilityArguments.function_schema(arguments_format=True)
        print("Arguments", args)
        return args

    async def __call__(
        self, ImportAbilityArguments: dict, **kwargs
    ) -> Context:
        url = f"{ARAP_BASE_URL}/api/v1/saas-apis/sales/"
        header = ImportAbilityArguments["header"]
        json_data = ImportAbilityArguments["json_data"]
        print(self.name(), header, json_data)
        data = json.dumps({"saleData": json_data})
        response = requests.request("POST", url, headers=header, data=data)
        text = "api_response:" + response.text
        return Context(
            [await self.get_content_item(text, header, url)]
        )

    async def get_content_item(
        self, content: str, header: dict, url: str = None
    ) -> Content:
        return Content.add_content_item(
            content,
            ContentType.DICT,
            source=url,
            content_metadata={"header": header},
        )


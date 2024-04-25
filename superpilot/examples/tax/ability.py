import json
import logging
from typing import List

import requests
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.configuration import Config
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.environment import Environment
from superpilot.core.planning.settings import LanguageModelConfiguration
from superpilot.core.planning.strategies import SummarizerStrategy
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.framework.tools.search_engine import SearchEngine, SearchEngineType
from superpilot.core.resource.model_providers import (
    SchemaModel,
)
from superpilot.examples.tax.gstr1_data_transformer_prompt import (
    Item,
    Document,
    DataList,
)
from pydantic import Field

# from services.taxgptservice.api.config import settings
ARAP_BASE_URL = "https://qa-arapback.mastersindia.co"


class Gstr1DataTransformAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.Gstr1DataTransformAbility",
        ),
        language_model_required=LanguageModelConfiguration(
            model_name=OpenAIModelName.GPT3_16K,
            provider_name=ModelProviderName.OPENAI,
            temperature=0.9,
        ),
    )


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
        # if not isinstance(json_data, str):
        #     json_data = json.dumps(json_data)
        data = {"saleData": json_data}
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


class GSRT1DataUploadAbility(Ability):
    default_configuration = AbilityConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.GSRT1DataUploadAbility",
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
        self._language_model_provider = environment.get("model_providers").get(
            configuration.language_model_required.provider_name
        )
        self._search_engine = SearchEngine(
            config=self._env_config, engine=SearchEngineType.DIRECT_GOOGLE
        )

        if prompt_strategy is None:
            prompt_strategy = SummarizerStrategy(
                model_classification=SummarizerStrategy.default_configuration.model_classification,
                system_prompt=SummarizerStrategy.default_configuration.system_prompt,
                user_prompt_template=SummarizerStrategy.default_configuration.user_prompt_template,
            )
        self._prompt_strategy = prompt_strategy

    @classmethod
    def description(cls) -> str:
        return "Upload GSTR1 Data to Government Portal"

    @classmethod
    def arguments(cls) -> dict:
        return {
            "header": {
                "type": "object",
                "properties": {
                    "gstin": {
                        "type": "string",
                        "description": "GSTIN (Goods and Services Tax Identification Number).",
                    },
                    "month": {"type": "string", "description": "Month in MM format."},
                    "year": {
                        "type": "string",
                        "description": "Year or year range in YYYY-YY format.",
                    },
                    "invoice": {
                        "type": "string",
                        "description": "Indicator for invoice ('Y' or 'N').",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Indicator for summary ('Y' or 'N').",
                    },
                    "MiplApiKey": {
                        "type": "string",
                        "description": "API Key for MIPL (Mandatory Invoice Parameters List).",
                    },
                    "Content-Type": {"type": "string", "description": "Content type."},
                },
                "description": "Details for GST invoice and related information.",
            }
        }

    async def __call__(self, header: dict, json_data: dict, **kwargs) -> Context:
        url = f"{ARAP_BASE_URL}/api/v1/saas-apis/upload-gstr1/"
        response = requests.request("POST", url, headers=header, json=json_data)
        print(response.text)
        return Context([await self.get_content_item(response.text, header, None)])

    async def get_content_item(self, content: str, header: dict, url: None) -> Content:
        return Content.add_content_item(
            content, ContentType.DICT, source=url, content_metadata={"header": header}
        )


from pydantic import Field


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
        # response = await test_pilot(sales_api_response)
        print(api_response)
        return Context([await self.get_content_item(str(api_response))])

    async def get_content_item(self, content: str) -> Content:
        return Content.add_content_item(content, ContentType.DICT)



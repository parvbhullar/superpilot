import logging
from typing import List

import requests
from superpilot.core.ability.base import Ability, AbilityConfiguration
from superpilot.core.configuration import Config
from superpilot.core.context.schema import Context, Content, ContentType
from superpilot.core.environment import Environment
from superpilot.core.planning.simple import LanguageModelConfiguration
from superpilot.core.planning.strategies import SummarizerStrategy
from superpilot.core.plugin.simple import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.framework.tools.search_engine import SearchEngine, SearchEngineType

# from services.taxgptservice.api.config import settings
ARAP_BASE_URL = "https://qa-arapback.mastersindia.co/"


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
        return {
            "header": {
                "type": "object",
                "properties": {
                    "gstin": {
                        "type": "string",
                        "description": "GSTIN (Goods and Services Tax Identification Number)."
                    },
                    "month": {
                        "type": "string",
                        "description": "Month in MM format."
                    },
                    "year": {
                        "type": "string",
                        "description": "Year or year range in YYYY-YY format."
                    },
                    "invoice": {
                        "type": "string",
                        "description": "Indicator for invoice ('Y' or 'N')."
                    },
                    "summary": {
                        "type": "string",
                        "description": "Indicator for summary ('Y' or 'N')."
                    },
                    "MiplApiKey": {
                        "type": "string",
                        "description": "API Key for MIPL (Mandatory Invoice Parameters List)."
                    },
                    "Content-Type": {
                        "type": "string",
                        "description": "Content type."
                    }
                },
                "description": "Details for GST invoice and related information."
            },
            "json_data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "document_number": {
                            "type": "string",
                            "description": "The document number."
                        },
                        "document_date": {
                            "type": "string",
                            "description": "The date of the document in DD-MM-YYYY format."
                        },
                        "original_document_number": {
                            "type": "string",
                            "description": "The original document number."
                        },
                        "original_document_date": {
                            "type": "string",
                            "description": "The original document date in DD-MM-YYYY format."
                        },
                        "ref_document_number": {
                            "type": "string",
                            "description": "The reference document number."
                        },
                        "ref_document_date": {
                            "type": "string",
                            "description": "The reference document date in DD-MM-YYYY format."
                        },
                        "supply_type": {
                            "type": "string",
                            "description": "Type of supply."
                        },
                        "invoice_status": {
                            "type": "string",
                            "description": "Status of the invoice."
                        },
                        "invoice_category": {
                            "type": "string",
                            "description": "Category of the invoice."
                        },
                        "invoice_type": {
                            "type": "string",
                            "description": "Type of the invoice."
                        },
                        "total_invoice_value": {
                            "type": "number",
                            "description": "Total value of the invoice."
                        },
                        "total_taxable_value": {
                            "type": "number",
                            "description": "Total taxable value."
                        },
                        "txpd_taxtable_value": {
                            "type": "number",
                            "description": "Taxable value."
                        },
                        "shipping_bill_number": {
                            "type": "string",
                            "description": "Shipping bill number."
                        },
                        "shipping_bill_date": {
                            "type": "string",
                            "description": "Shipping bill date in DD-MM-YYYY format."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the transaction."
                        },
                        "port_code": {
                            "type": "string",
                            "description": "Port code."
                        },
                        "location": {
                            "type": "string",
                            "description": "Location."
                        },
                        "gstr1_return_period": {
                            "type": "string",
                            "description": "Return period for GSTR-1."
                        },
                        "gstr3b_return_period": {
                            "type": "string",
                            "description": "Return period for GSTR-3B."
                        },
                        "reverse_charge": {
                            "type": "string",
                            "description": "Reverse charge information."
                        },
                        "isamended": {
                            "type": "string",
                            "description": "Information about whether the invoice is amended."
                        },
                        "amended_pos": {
                            "type": "string",
                            "description": "Amended place of supply."
                        },
                        "amended_period": {
                            "type": "string",
                            "description": "Period for which the invoice is amended."
                        },
                        "place_of_supply": {
                            "type": "string",
                            "description": "Place of supply."
                        },
                        "supplier_gstin": {
                            "type": "string",
                            "description": "GSTIN of the supplier."
                        },
                        "buyer_gstin": {
                            "type": "string",
                            "description": "GSTIN of the buyer."
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Name of the customer."
                        },
                        "amortised_cost": {
                            "type": "string",
                            "description": "Information about amortised cost."
                        },
                        "itemList": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "hsn_code": {
                                        "type": "string",
                                        "description": "HSN code."
                                    },
                                    "quantity": {
                                        "type": "number",
                                        "description": "Quantity of the item."
                                    },
                                    "unit_of_product": {
                                        "type": "string",
                                        "description": "Unit of the product."
                                    },
                                    "gst_rate": {
                                        "type": "number",
                                        "description": "GST rate."
                                    },
                                    "cess_amount": {
                                        "type": "number",
                                        "description": "CESS amount."
                                    },
                                    "taxable_value": {
                                        "type": "number",
                                        "description": "Taxable value of the item."
                                    },
                                    "cgst_amount": {
                                        "type": "number",
                                        "description": "CGST amount."
                                    },
                                    "sgst_amount": {
                                        "type": "number",
                                        "description": "SGST amount."
                                    },
                                    "igst_amount": {
                                        "type": "number",
                                        "description": "IGST amount."
                                    },
                                    "item_description": {
                                        "type": "string",
                                        "description": "Description of the item."
                                    },
                                    "product_name": {
                                        "type": "string",
                                        "description": "Name of the product."
                                    },
                                    "invoice_value": {
                                        "type": "number",
                                        "description": "Value of the invoice for the item."
                                    }
                                }
                            },
                            "description": "List of items in the invoice."
                        },
                        "error": {
                            "type": "object",
                            "properties": {
                                "GEAEIN": {
                                    "type": "string",
                                    "description": "Error message - GEAEIN."
                                }
                            },
                            "description": "Error information."
                        }
                    }
                },
                "description": "A list of invoices."
            }
        }

    async def __call__(self, header: dict, json_data: List[dict], **kwargs) -> Context:
        url = f"{ARAP_BASE_URL}/api/v1/saas-apis/sales/"
        print(self.name(), header, json_data)
        response = requests.request("POST", url, headers=header, data=json_data)
        print(response.text)
        return Context([await self.get_content_item(response.text, header, json_data, None)])

    async def get_content_item(self, content: str, header: dict, json_data: List[dict], url: str) -> Content:
        return Content.add_content_item(content, ContentType.DICT, source=url,
                                        content_metadata={'header': header, 'json_data': json_data})


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
                        "description": "GSTIN (Goods and Services Tax Identification Number)."
                    },
                    "month": {
                        "type": "string",
                        "description": "Month in MM format."
                    },
                    "year": {
                        "type": "string",
                        "description": "Year or year range in YYYY-YY format."
                    },
                    "invoice": {
                        "type": "string",
                        "description": "Indicator for invoice ('Y' or 'N')."
                    },
                    "summary": {
                        "type": "string",
                        "description": "Indicator for summary ('Y' or 'N')."
                    },
                    "MiplApiKey": {
                        "type": "string",
                        "description": "API Key for MIPL (Mandatory Invoice Parameters List)."
                    },
                    "Content-Type": {
                        "type": "string",
                        "description": "Content type."
                    }
                },
                "description": "Details for GST invoice and related information."
            }
        }

    async def __call__(self, header: dict, json_data: dict, **kwargs) -> Context:
        url = f"{ARAP_BASE_URL}/api/v1/saas-apis/upload-gstr1/"
        response = requests.request("POST", url, headers=header, json=json_data)
        print(response.text)
        return Context([await self.get_content_item(response.text, header, None)])

    async def get_content_item(self, content: str, header: dict, url: None) -> Content:
        return Content.add_content_item(
            content, ContentType.DICT, source=url, content_metadata={'header': header}
        )

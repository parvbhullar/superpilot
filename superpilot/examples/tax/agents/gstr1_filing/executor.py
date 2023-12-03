import os

from services.gstgptservice.agents.gstr1_filing.pilots.super_pilot import SuperPilot
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.core.configuration.config import get_config
from superpilot.core.context.schema import Content, ContentType
from superpilot.core.context.schema import Context
from superpilot.core.pilot.chain.simple import SimpleChain
from superpilot.core.pilot.settings import (
    PilotConfiguration,
    ExecutionAlgo
)
from superpilot.core.pilot.task.base import TaskPilotConfiguration
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.pilot.task.super import SuperTaskPilot
from superpilot.core.planning import strategies
from superpilot.core.planning.schema import (
    ExecutionNature,
)
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    LanguageModelClassification,
)
from superpilot.core.plugin.simple import (
    PluginLocation,
    PluginStorageFormat,
)
from superpilot.core.resource.model_providers import (
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.examples.executor.base import BaseExecutor
from superpilot.tests.test_env_simple import get_env

from services.gstgptservice.agents.gstr1_filing.abilities.api_response_observer_ability import \
    ApiResponseObserverAbility
from services.gstgptservice.agents.gstr1_filing.abilities.gstr1_data_upload_ability import GSRT1DataUploadAbility
from services.gstgptservice.agents.gstr1_filing.abilities.sale_data_import_ability import SalesDataImportAbility
from services.gstgptservice.agents.gstr1_filing.gstr1_data_transformer_prompt import GSTR1DataTransformerPrompt
from services.gstgptservice.agents.gstr1_filing.abilities.gstr1_data_summary import GSRT1SummaryAbility


class Gstr1FillingExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()
    config = get_config()
    chain = SimpleChain()
    env = get_env({})
    ALLOWED_ABILITY = {
        # Gstr1DataTransformAbility.name(): Gstr1DataTransformAbility.default_configuration,
        SalesDataImportAbility.name(): SalesDataImportAbility.default_configuration,
        GSRT1DataUploadAbility.name(): GSRT1DataUploadAbility.default_configuration,
        GSRT1SummaryAbility.name(): GSRT1SummaryAbility.default_configuration,
    }

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        ability_registry = SuperAbilityRegistry.factory(self.env, self.ALLOWED_ABILITY)
        self.api_pilot = SuperPilot(
            ability_registry=ability_registry, 
            model_providers=self.model_providers,
            configuration= TaskPilotConfiguration(
                location=PluginLocation(
                    storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
                    storage_route="superpilot.core.flow.simple.SuperTaskPilot",
                ),
                pilot=PilotConfiguration(
                    name="super_task_pilot",
                    role=(
                        "An AI Pilot designed to complete simple tasks with "
                    ),
                    goals=[
                        "Complete simple tasks",
                    ],
                    cycle_count=0,
                    max_task_cycle_count=3,
                    creation_time="",
                    execution_algo=ExecutionAlgo.PLAN_AND_EXECUTE,
                ),
                execution_nature=ExecutionNature.AUTO,
                prompt_strategy=strategies.NextAbility.default_configuration,
                models={
                    LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                        model_name=OpenAIModelName.GPT3,
                        provider_name=ModelProviderName.OPENAI,
                        temperature=0.9,
                    ),
                    LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                        model_name=OpenAIModelName.GPT4_TURBO,
                        provider_name=ModelProviderName.OPENAI,
                        temperature=0.9,
                    ),
                },
            ),
        )
        transformer_pilot = SimpleTaskPilot.create(
            GSTR1DataTransformerPrompt.default_configuration,
            model_providers=self.model_providers,
            smart_model_name=OpenAIModelName.GPT4_TURBO,
            fast_model_name=OpenAIModelName.GPT3,
        )

        # vision_pilot = SimpleTaskPilot.create(
        #     DescribeQFigurePrompt.default_configuration,
        #     model_providers=self.model_providers,
        #     smart_model_name=OpenAIModelName.GPT4_VISION,
        #     fast_model_name=OpenAIModelName.GPT3,
        # )
        # solver_pilot = SimpleTaskPilot.create(
        #     SolutionValidatorPrompt.default_configuration,
        #     model_providers=self.model_providers,
        #     smart_model_name=AnthropicModelName.CLAUD_2,
        #     fast_model_name=AnthropicModelName.CLAUD_2_INSTANT,
        # )
        # format_pilot = SimpleTaskPilot.create(
        #     SolutionValidatorPrompt.default_configuration,
        #     model_providers=self.model_providers,
        #     smart_model_name=OpenAIModelName.GPT4_TURBO,
        #     fast_model_name=OpenAIModelName.GPT3,
        # )

        # self.chain.add_handler(transformer_pilot, self.data_transformer)
        # self.chain.add_handler(self.sample_chain_function, self.sample_chain_function)
        self.chain.add_handler(self.api_pilot, self.format_transformer)

    def sample_chain_function(self, data, response, context):
        print("Sample chain Task: ", data)

    def data_transformer(self, data, response, context):
        print("data transformer", response)
        # task = json.dumps(response.contesnt)
        data = response.content
        data.update({'header': {
            'gstin': os.environ.get('GSTIN'),
            'month': '04',
            'year': '2023-24',
            'invoice': 'Y',
            'summary': 'N',
            'MiplApiKey': os.environ.get('MIPL_API_KEY'),
            "Content-Type": "application/json"
        }})
        task = self.PROMPT_TEMPLATE.format(**data)
        # print(task)
        return task, context

    # def solver_transformer(self, data, response, context):
    #     response = {
    #         "question": data,
    #         "solution": response.get("completion", ""),
    #     }
    #     task = self.PROMPT_TEMPLATE.format(**response)
    #     return task, context

    def format_transformer(self, data, response, context):
        # print("format_transformer", response)
        task = response.dict()
        context = response
        # print(task)
        return task, context

    PROMPT_TEMPLATE = """
            Documents:{documents}

            Header:{header}
            """

    async def execute(self, task: str, **kwargs):
        task = {
            'documents': [
                {
                    "document_number": "GPT1",
                    "document_date": "04-04-2023",
                    "original_document_number": "",
                    "original_document_date": "",
                    "ref_document_number": "",
                    "ref_document_date": "",
                    "supply_type": "NOR",
                    "invoice_status": "Add",
                    "invoice_category": "TXN",
                    "invoice_type": "R",
                    "total_invoice_value": 59,
                    "total_taxable_value": 50,
                    "txpd_taxtable_value": 59,
                    "shipping_bill_number": "",
                    "shipping_bill_date": "",
                    "reason": "",
                    "port_code": "",
                    "location": "Haridwar",
                    "gstr1_return_period": "",
                    "gstr3b_return_period": "",
                    "reverse_charge": "",
                    "isamended": "",
                    "amended_pos": "",
                    "amended_period": "",
                    "place_of_supply": "05",
                    "supplier_gstin": "33GSPTN0591G1Z7",
                    "buyer_gstin": "06AAJCS9091D1Z4",
                    "customer_name": "CMR Green Technologies Limited",
                    "amortised_cost": "N",
                    "itemList": [
                        {
                            "hsn_code": "68126011",
                            "quantity": 10,
                            "unit_of_product": "NOS",
                            "gst_rate": 18,
                            "cess_amount": 0,
                            "taxable_value": 50,
                            "cgst_amount": 0,
                            "sgst_amount": 0,
                            "igst_amount": 9,
                            "item_description": "CABLE GLAND 1/2 PVC-PG-09",
                            "product_name": "CABLE GLAND 1/2 PVC-PG-09",
                            "invoice_value": 1
                        }
                    ]
                }
            ],
            'header': {
                'gstin': "27GSPMH0591G1ZK",
                'month': '04',
                'year': '2023-24',
                'invoice': 'Y',
                'summary': 'N',
                'MiplApiKey': "SiZYXl7CNXy7QiGrymKf7dJXpvCxWtfr",
                "Content-Type": "application/json"
            }
        }
        self.context.add(Content.add_content_item(
            self.PROMPT_TEMPLATE.format(**task), ContentType.DICT
        ))
        # task = """
        # Use given data to fill import sales invoices, then observe the response given from sale import api, 
        # show the invoice summary of gstr1,then upload the invoices in gstr1,
        # your ending point is to get the response from gstr1 upload api.
        # """
        task = "hi there"

        # task = Task.factory(task, **kwargs)
        # response = await self.api_pilot.execute(task, self.context, **kwargs)
        response, context = await self.chain.execute(task, self.context, **kwargs)
        print(response)
        return response

    async def run(self, context):
        response = await self.execute(context)
        # print(response)
        return response

# "user input" -> back and forth-> "current flow"
# 5-6, 1-2

# file gstr1 return -> sales import data mango

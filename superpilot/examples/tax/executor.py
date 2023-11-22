import json
import os

from superpilot.core.pilot.chain.simple import SimpleChain
from superpilot.examples.executor.base import BaseExecutor
from superpilot.core.context.schema import Context

from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.pilot.task.super import SuperTaskPilot
from superpilot.core.resource.model_providers.factory import ModelProviderFactory
from superpilot.tests.test_env_simple import get_env
from superpilot.core.configuration.config import get_config
from superpilot.core.ability.super import SuperAbilityRegistry
from superpilot.examples.tax.ability import Gstr1DataTransformAbility, SalesDataImportAbility
from superpilot.examples.tax.gstr1_data_transformer_prompt import GSTR1DataTransformerPrompt
from superpilot.core.resource.model_providers import (
    OpenAIModelName,
)
from superpilot.core.planning.schema import (
    Task,
)


class Gstr1FillingExecutor(BaseExecutor):
    model_providers = ModelProviderFactory.load_providers()
    context = Context()
    config = get_config()
    chain = SimpleChain()
    env = get_env({})
    ALLOWED_ABILITY = {
        # Gstr1DataTransformAbility.name(): Gstr1DataTransformAbility.default_configuration,
        SalesDataImportAbility.name(): SalesDataImportAbility.default_configuration,
    }

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        ability_registry = SuperAbilityRegistry.factory(self.env, self.ALLOWED_ABILITY)
        self.api_pilot = SuperTaskPilot(ability_registry, self.model_providers)
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

        self.chain.add_handler(transformer_pilot, self.data_transformer)
        # self.chain.add_handler(self.sample_chain_function, self.sample_chain_function)
        self.chain.add_handler(self.api_pilot, self.format_transformer)

    def sample_chain_function(self, data, response, context):
        print("Sample chain Task: ", data)

    def data_transformer(self, data, response, context):
        # print("data transformer", response)
        # task = json.dumps(response.content)
        task = self.PROMPT_TEMPLATE.format(**response.content)
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
        print("format_transformer", response)
        task = response.get("documents", "")
        # print(task)
        return task, context

    PROMPT_TEMPLATE = """
            Documents:{documents}
            
            Header:{header}
            """

    async def execute(self, task: str, **kwargs):
        task = {'documents': [{'document_number': '800/50', 'document_date': '29-08-2021', 'supply_type': 'Normal', 'invoice_status': 'Add', 'invoice_category': '', 'invoice_type': 'Tax Invoice', 'total_invoice_value': 3068, 'total_taxable_value': 45600.56, 'txpd_taxtable_value': 0, 'location': 'Delhi', 'gstr1_return_period': '08-2021', 'gstr3b_return_period': '082021', 'reverse_charge': '', 'place_of_supply': '9', 'supplier_gstin': '27GSPMH0591G1ZK', 'buyer_gstin': '33GSPTN9511G3Z3', 'customer_name': 'IPM INDIA WHOLESALE TRADING PVT LTD', 'amortised_cost': '', 'itemList': [{'hsn_code': '0208', 'quantity': 25.56, 'unit_of_product': 'KGS', 'gst_rate': 18, 'cess_amount': 25.65, 'taxable_value': 45600.56, 'cgst_amount': 0, 'sgst_amount': 0, 'igst_amount': 8208.1008, 'item_description': '', 'product_name': '', 'invoice_value': 3068}]}, {'document_number': '800/51', 'document_date': '29-08-2021', 'supply_type': 'Normal', 'invoice_status': 'Add', 'invoice_category': '', 'invoice_type': 'Tax Invoice', 'total_invoice_value': 3068, 'total_taxable_value': 85900.56, 'txpd_taxtable_value': 0, 'location': 'Delhi', 'gstr1_return_period': '08-2021', 'gstr3b_return_period': '082021', 'reverse_charge': '', 'place_of_supply': '27', 'supplier_gstin': '27GSPMH0591G1ZK', 'buyer_gstin': '33GSPTN9511G3Z3', 'customer_name': 'IPM INDIA WHOLESALE TRADING PVT LTD', 'amortised_cost': '', 'itemList': [{'hsn_code': '0208', 'quantity': 25.56, 'unit_of_product': 'KGS', 'gst_rate': 18, 'cess_amount': 50.56, 'taxable_value': 85900.56, 'cgst_amount': 7731.0504, 'sgst_amount': 7731.0504, 'igst_amount': 0, 'item_description': '', 'product_name': '', 'invoice_value': 3068}]}]
                    , 'header':{
                        'gstin': os.environ.get('GSTIN'),
                        'month': '04',
                        'year': '2023-24',
                        'invoice': 'Y',
                        'summary': 'N',
                        'MiplApiKey': os.environ.get('MIPL_API_KEY'),
                        "Content-Type": "application/json"
                    }
                }
        task = self.PROMPT_TEMPLATE.format(**task)
        task = Task.factory(task, **kwargs)
        response = await self.api_pilot.execute(task, self.context, **kwargs)
        # response, context = await self.chain.execute(task, self.context, **kwargs)
        print(response)
        return response

    async def run(self, context):
        response = await self.execute(context)
        print(response)
        return response

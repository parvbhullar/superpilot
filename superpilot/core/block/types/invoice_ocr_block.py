import logging
import os
from urllib.parse import urlparse

import boto3
import requests

from superpilot.core.block.base import Block, BlockConfiguration
from superpilot.core.pilot.settings import PilotConfiguration, ExecutionNature
from superpilot.core.pilot.task.settings import TaskPilotConfiguration
from superpilot.core.pilot.task.simple import SimpleTaskPilot
from superpilot.core.planning import LanguageModelClassification, Task
from superpilot.core.planning.settings import LanguageModelConfiguration, PromptStrategyConfiguration
from superpilot.core.planning.strategies.simple import SimplePrompt
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat
from superpilot.core.resource.model_providers import OpenAIModelName, ModelProviderName
from superpilot.core.workspace import Workspace


model_mapping = {
    ModelProviderName.OPENAI: {
        'ADA': OpenAIModelName.ADA,
        'GPT3': OpenAIModelName.GPT3,
        'GPT3_16K': OpenAIModelName.GPT3_16K,
        'GPT4': OpenAIModelName.GPT4,
        'GPT4_32K': OpenAIModelName.GPT4_32K,
        'GPT4_TURBO': OpenAIModelName.GPT4_TURBO,
        'GPT4_VISION': OpenAIModelName.GPT4_VISION,
        'GPT4_32K_NEW': OpenAIModelName.GPT4_32K_NEW,
        'GPT3_FINETUNE_MODEL': OpenAIModelName.GPT3_FINETUNE_MODEL,
        'GPT4_O': OpenAIModelName.GPT4_O
    }
}

model_provider_mapping = {'OPEN_AI': ModelProviderName.OPENAI}


class InvoiceOCRBlock(Block):
    default_configuration = BlockConfiguration(
        id=0,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.InvoiceOCRBlock",
        ),
        block_type="invoice_ocr_block",
        metadata={
            "name": "invoice_ocr_block",
            "description": "A block that uses a language model to generate text.",
            "config": {}
        },
        input_schema={
            "document_type": {
                "type": "string",
                "description": "The genre of the story.",
            }
        },
        output_schema={
            "response": {
                "type": "object",
                "description": "The output of the block.",
            },
        },
        body="",
        seq_order=0
    )

    def __init__(
        self,
        logger: logging.Logger,
        configuration: BlockConfiguration,

    ):
        self._logger = logger
        self._configuration = configuration

    @property
    def description(self) -> str:
        return "LLM block."

    @property
    def config(self) -> str:
        return self._configuration

    @property
    def arguments(self) -> dict:
        return {
            "model_name": {
                "type": "string",
                "description": "The name of the model to use.",
            },
            "model_temp": {
                "type": "string",
                "description": "Temp of the model to use.",
            },
            "system_prompt": {
                "type": "string",
                "description": "The system prompt to use.",
            },
        }

    def read_file_from_s3(self, http_url):
        return requests.get(http_url).content

    async def __call__(self, **invoice_ocr_args: dict) -> dict:
        print("LLM block called.", )
        document_type = invoice_ocr_args.get("document_type")
        file_url = invoice_ocr_args.get("file_url", '')
        jwt = invoice_ocr_args.get("jwt", '')
        url = "https://pre-arapback.mastersindia.co/api/v2/ocr/upload/"

        payload = {}

        file_content = self.read_file_from_s3(file_url)
        file_name = 'invoice.pdf'

        files = [
          ('file_url', (file_name, file_content, 'application/pdf'))
        ]
        headers = {
            'Authorization': f'JWT {jwt}',
            'Mode': 'Buyer',
            'Productid': 'arap',
            'Subid': '5444',
            'mode': 'Buyer'
        }

        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        res = response.json()

        return res



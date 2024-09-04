import os
import sys

from superpilot.core.block.types.invoice_ocr_block import InvoiceOCRBlock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.block.types.api_block import APIBlock
from superpilot.core.block.types.form_block import FormBlock
from superpilot.core.block.execution.simple import SimpleExecutor
from superpilot.core.logging.logging import get_logger

from superpilot.core.block.simple import SimpleBlockRegistry
from superpilot.core.block.types.llm_block import LLMBlock

import datetime
from superpilot.core.block.base import BlockConfiguration
import asyncio

json_data = [
    {
        "id": 1,
        "location": FormBlock.default_configuration.location,
        "block_type": "form",
        "metadata": {
            "name": "form Block",
            "description": "Form To get values",
            "config": {}
        },
        "input_schema": {
            "document_type": {
                "type": "string",
                "description": "Invoice type",
                "value": "BOE"
            }
        },
        "output_schema": {},
        "body": "",
        "seq_order": 0
    },
    {
        "id": 2,
        "location": InvoiceOCRBlock.default_configuration.location,
        "block_type": "invoice_ocr_block",
        "metadata": {
            "name": "invoice_ocr_block",
            "description": "A block that uses a language model to generate text.",
            "config": {}
        },
        "input_schema": {
            "document_type": {
                "type": "string",
                "description": "document type",
                "reference": "block_1.document_type"
            },
            "file_url": {
                "type": "string",
                "description": "file url",
                "reference": "block_1.file_url"
            }
        },
        "output_schema": {
            "response": {
                "type": "object",
                "description": "The output of the block.",
            },
        },
        "body": "",
        "seq_order": 1
    }

]


async def execution():
    BLOCKS = {}

    for block in json_data:
        b = BlockConfiguration.factory(block)
        BLOCKS[str(b.id)] = b
        # print("\n\n", b)

    block_registry = SimpleBlockRegistry(BLOCKS)
    logger = get_logger(__name__)

    executor = SimpleExecutor(block_registry, logger)
    res = await executor.execute(**{"document_type": "BOE", "file_url": "https://unpodbackend.s3.amazonaws.com/media/private/Charger-Bill.pdf"})
    # res = await executor.execute(**{"gstin": "09AAHCC6805B1ZW"})

    print(res)



if __name__ == "__main__":
    asyncio.run(execution())

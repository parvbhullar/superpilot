import os
import sys

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
        "id": 0,
        "location": FormBlock.default_configuration.location,
        "block_type": "form",
        "metadata": {
            "name": "form Block",
            "description": "Form To get values",
            "config": {}
        },
        "input_schema": {
            "gstin": {
                "type": "string",
                "description": "The GSTIN to search for.",
                "value": "09AAHCC6805B1ZW"

            }
        },
        "output_schema": {},
        "body": "",
        "seq_order": 0
    },
    {
        "id": 1,
        "location": APIBlock.default_configuration.location,
        "block_type": "api",
        "metadata": {
            "name": "API Block",
            "description": "A block that interacts with the API.",
            "config": {
                "url": "https://commonapi.mastersindia.co/commonapis/searchgstin",
                "method": "GET",
                "headers": {
                    "Authorization": "Bearer 9064e672f30ed03e2ac8e24d86279e7f36c2bd82",
                    "client_id": "JarZChUcsytSBbnkpt"
                }
            }
        },
        "input_schema": {
            "query_params": {
                "type": "object",
                "properties": {
                    "gstin": {
                        "type": "string",
                        "description": "The GSTIN to search for.",
                        "reference": "block_0.gstin",
                        "value": "block_0.gstin"
                    }
                }
            }, 
            "headers": {},
            "payload": {}
        },
        "output_schema": {
            "response": {
                "type": "object",
                "description": "The response from the API."
            }
        },
        "body": "",
        "seq_order": 0
    },
    {
        "id": 2,
        "location": LLMBlock.default_configuration.location,
        "block_type": "llm",
        "metadata": {
            "name": "llm",
            "description": "A block that uses a language model to generate text.",
            "config": {
                "model_name": "gpt-3.5-turbo",
                "model_temp": "0.5",
                "model_provider": "OPEN_AI",
                "system_prompt": "You are a smart AI agent which will create summary of a particular businesss gstin status from given response in json. Do not mention in this data or json, just response as simplistic manner."
            }
        },
        "input_schema": {
            "gstin_data": {
                "type": "object",
                "description": "The response from the API.",
                "reference": "block_1.response",
                "value": ""
            }
        },
        "output_schema": {
            "response": {
                "type": "string",
                "description": "The output of the block."
            }
        },
        "body": "",
        "seq_order": 0
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
    await executor.execute(**{"gstin": "09AAHCC6805B1ZW"})
    # res = await executor.execute(**{"gstin": "09AAHCC6805B1ZW"})



if __name__ == "__main__":
    asyncio.run(execution())

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.block.execution.simple import SimpleExecutor
from superpilot.core.logging.logging import get_logger

from superpilot.core.block.simple import SimpleBlockRegistry
from superpilot.core.block.types.llm_block import LLMBlock

import datetime
from superpilot.core.block.base import BlockConfiguration
import asyncio

json_data = [
        {
            'id': 5,
            'created': datetime.datetime(2024, 5, 19, 10, 45, 45, 827518),
            'modified': datetime.datetime(2024, 5, 19, 11, 13, 41, 317981),
            'created_by': None,
            'updated_by': None,
            'block_type': 'llm_model',
            'metadata': '{"name": "add", "language": "python", "description": "Block to add two numbers", "llm_input_var": "my_var"}',
            'seq_order': 3,
            'block_visibility': 1,
            'result_visibility': 1,
            'input_schema': {"num1": {"type": "string", "description": "String", "default_key": "block-id.sum_result"}},
            'output_schema': {
                'original_string': {'type': 'string', 'description': 'source string'},
                'translated_string': {'type': 'string', 'description': 'translated result string '}
            },
            'body': 'res = kwargs["num1"] + kwargs["num2"]\r\nif res >= 0:\r\n    ans = "greater"\r\nelse:\r\n    ans = "less"\r\nprint(ans)\r\nresult = ans',
            'superbook_id': 21,
            ""
            'location': LLMBlock.default_configuration.location
        },
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
    await executor.execute()


if __name__ == "__main__":
    asyncio.run(execution())
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
        # {
        #     'id': 4,
        #     'created': datetime.datetime(2024, 4, 30, 18, 38, 35, 596732),
        #     'modified': datetime.datetime(2024, 4, 30, 18, 40, 19, 84799),
        #     'created_by': None,
        #     'updated_by': None,
        #     'block_type': 'input_form',
        #     'metadata': '{}',
        #     'seq_order': 1,
        #     'block_visibility': 1,
        #     'result_visibility': 1,
        #     'input_schema': '[{"name": "statement", "type": "text", "title": "sentence", "required": true, "placeholder": "sentence", "defaultValue": "Hello"}, {"name": "source_language", "type": "select", "title": "Source Language", "choices": ["Hindi", "English", "Punjabi"], "required": true, "placeholder": "Single select", "defaultValue": "Hindi"}, {"name": "translation_language", "type": "select", "title": "Translation Language", "choices": ["English", "Hindi", "Punjabi", "Tamil"], "required": true, "placeholder": "Single select", "defaultValue": "English"}]',
        #     'output_schema': '[]',
        #     'body': '',
        #     'superbook_id': 21
        # },
        # {
        #     'id': 6,
        #     'created': datetime.datetime(2024, 5, 19, 10, 45, 48, 259347),
        #     'modified': datetime.datetime(2024, 5, 19, 11, 25, 4, 422073),
        #     'created_by': None,
        #     'updated_by': None,
        #     'block_type': 'code',
        #     'metadata': '{"language": "python"}',
        #     'seq_order': 2,
        #     'block_visibility': 1,
        #     'result_visibility': 1,
        #     'input_schema': '[]',
        #     'output_schema': '[]',
        #     'body': 'my_var = "What is 3 plus 2 minus 5"',
        #     'superbook_id': 21
        # },
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
            'input_schema': '{"num1": {"type": "number", "description": "The first number."}, "num2": {"type": "number", "description": "The second number."}}',
            'output_schema': '{}',
            'body': 'res = kwargs["num1"] + kwargs["num2"]\r\nif res >= 0:\r\n    ans = "greater"\r\nelse:\r\n    ans = "less"\r\nprint(ans)\r\nresult = ans',
            'superbook_id': 21,
            'location': LLMBlock.default_configuration.location
        },
        {
            'id': 3,
            'created': datetime.datetime(2024, 4, 1, 5, 22, 35, 599490),
            'modified': datetime.datetime(2024, 5, 19, 11, 13, 47, 749420),
            'created_by': None,
            'updated_by': None,
            'block_type': 'llm_model',
            'metadata': '{"name": "subtract", "language": "python", "description": "Block to subtract two numbers", "llm_input_var": "my_var"}',
            'seq_order': 4,
            'block_visibility': 1,
            'result_visibility': 1,
            'input_schema': '{"num1": {"type": "number", "description": "The first number."}, "num2": {"type": "number", "description": "The second number."}}',
            'output_schema': '{}',
            'body': 'res = kwargs["num1"] - kwargs["num2"]\r\nif res >= 0:\r\n    ans = "greater"\r\nelse:\r\n    ans = "less"\r\nprint(ans)\r\nprint(res)\r\nresult = ans',
            'superbook_id': 21,
            'location': LLMBlock.default_configuration.location
        },
        {
            'id': 2,
            'created': datetime.datetime(2024, 4, 1, 5, 17, 37, 532541),
            'modified': datetime.datetime(2024, 5, 19, 11, 19, 47, 938401),
            'created_by': None,
            'updated_by': None,
            'block_type': 'llm_model',
            'metadata': '{"name": "result", "language": "python", "description": "Result of operations", "llm_block_type": "llm_output", "llm_output_var": "my_llm_output"}',
            'seq_order': 5,
            'block_visibility': 1,
            'result_visibility': 1,
            'input_schema': '{}',
            'output_schema': '{"num": {"type": "number", "description": "result of calculations"}, "res": {"type": "string", "description": "summary of result"}}',
            'body': '',
            'superbook_id': 21,
            'location': LLMBlock.default_configuration.location
        },
        # {
        #     'id': 7,
        #     'created': datetime.datetime(2024, 5, 19, 11, 20, 5, 608776),
        #     'modified': datetime.datetime(2024, 5, 19, 11, 20, 57, 709155),
        #     'created_by': None,
        #     'updated_by': None,
        #     'block_type': 'code',
        #     'metadata': '{"language": "python"}',
        #     'seq_order': 6,
        #     'block_visibility': 1,
        #     'result_visibility': 1,
        #     'input_schema': '{"type": "array", "items": {"type": "string"}}',
        #     'output_schema': '{"type": "number"}',
        #     'body': 'print("this is output")\r\nprint(my_llm_output)',
        #     'superbook_id': 21
        # }
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
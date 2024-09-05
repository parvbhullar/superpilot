import os
import sys

import sqlite3 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.core.block.types.api_block import APIBlock
from superpilot.core.block.types.form_block import FormBlock
from superpilot.core.block.execution.simple import SimpleExecutor
from superpilot.core.logging.logging import get_logger

from superpilot.core.block.simple import SimpleBlockRegistry
from superpilot.core.block.types.llm_block import LLMBlock
from superpilot.core.block.types.sql_block import SQLBlock
import datetime
from superpilot.core.block.base import BlockConfiguration
import asyncio
import sqlite3 
# from superpilot.core.block.types.sql_block 
# import __call__
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
            "query": {
                "type": "string",
                "value": "select * from users;"

            }
        },
        "output_schema": {},
        "body": "",
        "seq_order": 0
    },
    {
        "id": 3,
        "location": SQLBlock.default_configuration.location,
        "block_type": "sql_query",
        "metadata": {
            "name": "sql",
            "description": "hi this block is to type sql query",
            "config": {
                "database_connection": "localhost",
                "database_name": "test_db",
                "database_port": "3306",
                "database_password":"z0987z0987",
                "database_username":"root"
            },
            "source_url": "http://example.com/sql-query-source" 
        },
        "input_schema": {
            "query": {
                "type": "sql_query",
                "value": "jsxkjabsjaqbs",     
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
 # or any other database connector you are using

def execute_sql_query(query, params):
    try:
        # Connect to the database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Execute the query with parameters
        cursor.execute(query, params)
        result = cursor.fetchall()
        # Close the connection
        conn.close()

        return result
    except sqlite3.Error as e:
        return {"error": str(e)}


#mapping of blocks
async def execution(json_data, input_type):
    BLOCKS = {} 

    for block in json_data:
        b = BlockConfiguration.factory(block)
        BLOCKS[str(b.id)] = b

    block_registry = SimpleBlockRegistry(BLOCKS)
    logger = get_logger(__name__)

    executor = SimpleExecutor(block_registry, logger)
    res = await executor.execute(**{"sql_query": "sql_query"})
    print(res,"res")

if __name__ == "__main__":
    asyncio.run(execution(json_data, input))



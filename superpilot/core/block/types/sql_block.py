import logging
from typing import Dict, Any
# import abstractmethod

import requests
import sqlalchemy
from typing import Dict, Any
from superpilot.core.block.base import Block, BlockConfiguration
from superpilot.core.plugin.base import PluginLocation, PluginStorageFormat


class SQLBlock(Block):
    default_configuration = BlockConfiguration(
        id=3,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route=f"{__name__}.SQLBlock",
        ),
        block_type="sql_query",
        metadata={
        "name": "sql",
        "description": "A block that processes SQL data and generates a summarized text response.",
        "config": {
                "database_connection": "localhost",
                "database_name": "test_db",
                "database_port": "3306",
                "database_password":"z0987z0987",
                "database_username":"root"
            },
        "source_url": "http://example.com/sql-query-source" 
            },
        
        input_schema={},  
        output_schema={
            "response": {
                "type": "sql_query",
                "description":  " The result set from the SQL query ",
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
        return "Sql Blog"

    @property
    def config(self) -> BlockConfiguration:
        return self._configuration

    @property
    def arguments(self) -> Dict[str, Any]:
        return self._configuration.input_schema

    async def __call__(self, **sql_kwargs) -> Dict[str, Any]:
        self._logger.info("SQL Block called.")

        config = self._configuration.metadata['config']

        # Assuming SQL connection and query details are provided in config
        # db_url = config['db_url']# Database connection URL
        query = sql_kwargs.get('query', '')  # SQL query passed from the caller
        params = sql_kwargs.get('params', {})  # Query parameters
        
        connection_parms=self._configuration.metadata['config']
        
        db_url = (
        f"mysql+pymysql://{connection_parms['database_username']}:{connection_parms['database_password']}"
        f"@{connection_parms['database_connection']}:{connection_parms['database_port']}/{connection_parms['database_name']}"

    )
        print(connection_parms,"connection params")
        # print("sql_kwargs", sql_kwargs)
        print(db_url,"url")
        print(sql_kwargs)
        print(query)
        print("query", query)
        
        # print("params", params)

        try:
            # Create a SQLAlchemy engine
            engine = sqlalchemy.create_engine(db_url)
            with engine.connect() as connection:
                # Execute the query with parameters if provided
               
                result = connection.execute(sqlalchemy.text(query))

                # Fetch all results
                rows = result.fetchall()
                # # Convert rows to a list of dictionaries
                result_list = [dict(row) for row in rows]
                print(result_list)

                # return {
                #     "response": result_list
                # }
        except sqlalchemy.exc.SQLAlchemyError as e:
            self._logger.error(f"An error occurred with the SQL query: {e}")
            return {
                "response": {
                    "status": "error",
                    "message": str(e)
                }
            }

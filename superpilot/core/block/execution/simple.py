import asyncio
import logging
import platform
import time
from typing import List, Dict, Any
import distro
import inflection

from superpilot.core.block.base import BlockRegistry, Block
from superpilot.core.block.execution.base import BaseExecutor
from superpilot.core.pilot.settings import ExecutionNature


class SimpleExecutor(BaseExecutor):

    default_configuration = {}

    def __init__(
            self,
            block_registry: BlockRegistry,
            logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self._logger = logger
        self._block_registry = block_registry
        self._execution_nature = ExecutionNature.SEQUENTIAL
        self._execution_state: Dict[str, Any] = {}

    # async def interaction_handler(self):
    async def execute(self, **kwargs):
        """Execute the task."""
        self._logger.debug(f"Executing task:")
        return await self.exec_blocks(**kwargs)

    async def exec_blocks(self, **kwargs) -> None:
        # Execute for Sequential nature
        for block in self._block_registry.blocks():
            try:
                block_input = self._prepare_block_input(block)
                response = await self._block_registry.perform(block.name(), **block_input)
                self._update_execution_state(block, response)
                self._logger.debug(f"Response from block {block.name()}: {response}")
            except Exception as e:
                    self._logger.error(f"Error executing block {block.name()}: {e}")
                    raise e
        return self._execution_state

    def _prepare_block_input(self, block: Block) -> Dict[str, Any]:
        block_input = {}
        for input_key, input_schema in block.config.input_schema.items():
            # TODO fetch respective block's id and key.
            reference_block_id = block.config.id
            if input_key in self._execution_state:
                block_input[input_key] = self._execution_state[reference_block_id][input_key]
                # TODO fetch respective block's id and key.
            elif input_schema[input_key].default_value in self._execution_state:
                block_input[input_key] = self._execution_state[reference_block_id][input_schema[input_key].default_value]
            else:
                self._logger.warning(f"Input '{input_key}' not found in execution state for block {block.name()}")
        return block_input

    def _update_execution_state(self, block: Block, response: Dict[str, Any]) -> None:
        for output_key in block.config.output_schema.keys():
            if output_key in response:
                self._execution_state[block.config.id][output_key] = response[output_key]
            else:
                self._logger.warning(f"Expected output '{output_key}' not found in response from block {block.name()}")

    def __repr__(self):
        pass

    def dump(self):
        pass


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info

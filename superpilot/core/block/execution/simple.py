import asyncio
import logging
import platform
import time
from typing import List, Dict
import distro
import inflection

from superpilot.core.block.base import BlockRegistry
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

    # async def interaction_handler(self):

    async def execute(self, **kwargs):
        """Execute the task."""
        self._logger.debug(f"Executing task:")
        await self.exec_blocks(**kwargs)

    async def exec_blocks(self, **kwargs) -> None:
        # Execute for Sequential nature
        for block in self._block_registry.blocks():
            try:
                print(block.dump(), kwargs)
                response = await self._block_registry.perform(block.name(), **kwargs)
                self._logger.debug(f"Response from block {block.name()}: {response}")
            except Exception as e:
                self._logger.error(f"Error executing block {block.name()}: {e}")
                raise e

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

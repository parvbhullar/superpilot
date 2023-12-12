import abc
import logging
from pathlib import Path
import inflection

from superpilot.core.callback.base import BaseCallback


class SimpleCallbackHandler(BaseCallback):
    async def on_chain_start(self, *args, **kwargs):
        print("SimpleCallbackHandler.on_chain_start")

    async def on_pilot_execute(self, *args, **kwargs):
        print("SimpleCallbackHandler.on_pilot_execute")

    async def on_ability_perform(self, *args, **kwargs):
        print("SimpleCallbackHandler.on_ability_perform")

    async def on_info(self, info, *args, **kwargs):
        print("Info: ", info)

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)


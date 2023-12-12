import abc
import logging
from pathlib import Path
import inflection

from superpilot.core.callback.base import BaseCallback


class BaseCallbackHandler(BaseCallback):
    @abc.abstractmethod
    async def on_chain_start(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def on_pilot_execute(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def on_ability_perform(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def on_clarifying_question(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def on_info(self, *args, **kwargs):
        ...

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)


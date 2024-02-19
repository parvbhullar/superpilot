import abc
import logging
from pathlib import Path
import inflection


class BaseCallback(abc.ABC):
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
    async def on_info(self, *args, **kwargs):
        ...

    async def on_observation_start(self, *args, **kwargs):
        pass

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

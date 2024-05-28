import abc
import logging
from pathlib import Path
import inflection


class Pilot(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def execute(self, *args, **kwargs):
        ...

    # @abc.abstractmethod
    # async def observe(self, *args, **kwargs):
    #     ...

    @abc.abstractmethod
    def __repr__(self):
        ...

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

    @abc.abstractmethod
    def dump(self):
        ...


class BasePilot(Pilot):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def initialize(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def plan(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def execute(self, *args, **kwargs):
        ...

    # @abc.abstractmethod
    # async def observe(self, *args, **kwargs):
    #     ...

    @abc.abstractmethod
    def dump(self):
        ...

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

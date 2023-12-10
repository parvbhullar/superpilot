import abc
import logging
import typing

from superpilot.core.state.mixins import DictStateMixin


class BaseState(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    async def save(self, *args, **kwargs) -> None:
        ...

    @abc.abstractmethod
    async def load(self, *args, **kwargs) -> dict:
        ...

    @classmethod
    @abc.abstractmethod
    async def load_from_dict(cls, obj: typing.Any, state: dict) -> None:
        ...

    @classmethod
    @abc.abstractmethod
    async def get_dict(cls, obj: typing.Any) -> dict:
        ...


class State(BaseState):
    def __init__(
        self,
        logger: logging.Logger = logging.getLogger(__name__),
        state: dict = None,
        *args,
        **kwargs
    ):
        self._logger = logger
        self._state = state or {}

    async def save(self, state: dict) -> None:
        self._state = state

    async def load(self, obj: DictStateMixin) -> dict:
        return self._state

    @classmethod
    async def load_from_dict(cls, obj: DictStateMixin, state: dict) -> None:
        if not hasattr(obj, 'from_dict_state'):
            raise Exception("Implement DictStateMixin")
        await obj.from_dict_state(state)

    @classmethod
    async def get_dict(cls, obj: DictStateMixin) -> dict:
        if not hasattr(obj, 'to_dict_state'):
            raise Exception("Implement DictStateMixin")
        return await obj.to_dict_state()

import abc
import logging
from pathlib import Path
import inflection


class Agent(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        ...

    @classmethod
    @abc.abstractmethod
    def from_workspace(
        cls,
        workspace_path: Path,
        logger: logging.Logger,
    ) -> "Agent":
        ...

    @abc.abstractmethod
    async def determine_next_ability(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    def __repr__(self):
        ...

    @classmethod
    def name(cls) -> str:
        """The name of the ability."""
        return inflection.underscore(cls.__name__)

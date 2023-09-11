from abc import ABC, abstractmethod
import inflection


class BaseExecutor(ABC):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @abstractmethod
    async def run(self, query):
        pass

    @classmethod
    def name(cls):
        return inflection.underscore(cls.__name__)

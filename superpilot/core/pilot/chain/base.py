from abc import ABC, abstractmethod
from enum import Enum
import logging


class HandlerType(Enum):
    HANDLER = "handler"
    OBSERVER = "observer"
    COMMUNICATOR = "communicator"


class BaseChain(ABC):
    def __init__(self,
                 logger: logging.Logger = logging.getLogger(__name__),
                 **kwargs):
        self.logger = logger
        self.pilots = {}
        self.transformers = {}

    def add_handler(self, handler, transformer=None):
        """
        Adds a handler and an optional transformer to the chain.
        """
        self._add(handler, transformer, HandlerType.HANDLER)

    def _add(self, pilot, transformer, pilot_type):
        if pilot_type not in self.pilots:
            self.pilots[pilot_type] = [pilot]
            self.transformers[pilot_type] = [transformer or None]
        else:
            self.pilots[pilot_type].append(pilot)
            self.transformers[pilot_type].append(transformer or None)

    def add_observer(self, observer, transformer=None):
        """
        Adds a handler and an optional transformer to the chain.
        """
        if HandlerType.OBSERVER in self.pilots:
            del self.pilots[HandlerType.OBSERVER]
            del self.transformers[HandlerType.OBSERVER]
        self._add(observer, transformer, HandlerType.OBSERVER)

    def current_observer(self):
        if HandlerType.OBSERVER not in self.pilots:
            return None
        return self.pilots[HandlerType.OBSERVER][-1]

    def current_handler(self, pilot_name):
        if HandlerType.HANDLER not in self.pilots:
            return None, None
        # TODO optimise this search
        for i, handler in enumerate(self.pilots[HandlerType.HANDLER]):
            if handler.name() == pilot_name:
                return handler, self.transformers[HandlerType.HANDLER][i]
        return None, None

    def default_transformer(self, data, response, context):
        response = response.get("content", data)
        return response, context

    @abstractmethod
    async def execute(self, data, context, **kwargs):
        pass

    def dump_pilots(self):
        pilots_dict = []
        for pilot in self.pilots[HandlerType.HANDLER]:
            pilots_dict.append(pilot.dump())

        return pilots_dict


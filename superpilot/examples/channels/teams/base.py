import abc
import logging
import inflection

logging.basicConfig(level=logging.INFO)


class bot(abc.ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.name())

    @abc.abstractmethod
    async def message_handler(self):
        """Connect to the messaging platform."""
        pass
    
    @abc.abstractmethod
    async def generate_response(self):
        """Connect to the messaging platform."""
        pass
    
    @abc.abstractmethod
    async def start(self):
        """Connect to the messaging platform."""
        pass


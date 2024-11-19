import abc
import logging
import inflection

logging.basicConfig(level=logging.INFO)


class BaseChannel(abc.ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.name())

    @abc.abstractmethod
    async def connect(self):
        """Connect to the messaging platform."""
        pass

    @abc.abstractmethod
    async def process_message(self, message):
        """Process incoming messages."""
        pass

    @abc.abstractmethod
    async def respond(self, channel, response_text):
        """Send a response to the messaging platform."""
        pass

    @classmethod
    def name(cls) -> str:
        """Returns a formatted name of the channel."""
        return inflection.underscore(cls.__name__)

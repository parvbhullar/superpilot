import abc
import logging


logging.basicConfig(level=logging.INFO)


class BaseChannel(abc.ABC):
    def get_access_token(self):
        self.logger = logging.getLogger(self.name())

    @abc.abstractmethod
    async def read_emails(self):
        """Connect to the messaging platform."""
        pass

    @abc.abstractmethod
    async def process_message(self, message):
        """Process incoming messages."""
        pass


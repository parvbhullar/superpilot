import abc
import logging


logging.basicConfig(level=logging.INFO)


class Baseoutlook(abc.ABC):
    def get_access_token(self):
        self.logger = logging.getLogger(self.name())

    @abc.abstractmethod
    async def send_email(self):
        """Connect to the messaging platform."""
        pass

    @abc.abstractmethod
    async def read_emails(self, message):
        """Process incoming messages."""
        pass


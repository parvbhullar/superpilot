import abc
import logging
import inflection

logging.basicConfig(level=logging.INFO)


class EmailProcessorBase(abc.ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.name())

    @abc.abstractmethod
    async def create_mongo_client(self):
        """Connect to a database or service."""
        pass

    @abc.abstractmethod
    async def store_email(self, message):
        """Store the email in a database."""
        pass

    @abc.abstractmethod
    def authenticate_gmail(self):
        """Authenticate with the Gmail API."""
        pass
    
    @abc.abstractmethod
    async def create_reply_message(self, message):
        """Store the email in a database."""
        pass

    
    @abc.abstractmethod
    async def send_reply(self, message):
        """Store the email in a database."""
        pass
    @abc.abstractmethod
    async def list_messages(self, message):
        """Store the email in a database."""
        pass
import abc
import logging
import inflection

logging.basicConfig(level=logging.INFO)


class BaseAgent(abc.ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.name())

    @abc.abstractmethod
    async def entrypoint(self, ctx):
        """Connect to the messaging platform."""
        pass

    @abc.abstractmethod
    async def run_multimodal_agent(self, ctx, participant):
        """Process incoming messages."""
        pass

    @abc.abstractmethod
    async def respond(self, message: str):
        """Send a response to the messaging platform."""
        pass
    
    @classmethod
    def check_env_vars(cls) -> str:
        """Returns a formatted name of the channel."""
        return inflection.underscore(cls.__name__)
    
    @classmethod
    def create_sip_participant(cls) -> str:
        """Returns a formatted name of the channel."""
        return inflection.underscore(cls.__name__)
    
    @classmethod
    def name(cls) -> str:
        """Returns a formatted name of the channel."""
        return inflection.underscore(cls.__name__)

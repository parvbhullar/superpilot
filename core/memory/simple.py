import json
import logging
from typing import List

from superpilot.core.configuration import Configurable
from superpilot.core.memory.base import Memory
from superpilot.core.memory.settings import MemoryConfiguration, MemorySettings
from superpilot.core.workspace import Workspace


class MessageHistory:
    def __init__(self, previous_message_history: List[str]):
        self._message_history = previous_message_history


class SimpleMemory(Memory, Configurable):
    default_settings = MemorySettings(
        name="simple_memory",
        description="A simple memory.",
        configuration=MemoryConfiguration(),
    )

    def __init__(
        self,
        settings: MemorySettings,
        logger: logging.Logger,
        workspace: Workspace,
    ):
        self._configuration = settings.configuration
        self._logger = logger
        self._message_history = self._load_message_history(workspace)

    @staticmethod
    def _load_message_history(workspace: Workspace):
        message_history_path = workspace.get_path("message_history.json")
        if message_history_path.exists():
            with message_history_path.open("r") as f:
                message_history = json.load(f)
        else:
            message_history = []
        return MessageHistory(message_history)

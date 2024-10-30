import logging
import pickle

from superpilot.core.context.schema import Context
from superpilot.core.state.base import BaseState
from superpilot.core.workspace import Workspace


class PickleState(BaseState):
    def __init__(
        self,
        thread_id: str,
        workspace: Workspace,
        logger: logging.Logger = logging.getLogger(__name__),
        *args,
        **kwargs
    ):
        super().__init__(logger, *args, **kwargs)
        self._thread_id = thread_id
        self._workspace = workspace

    async def save(self, context: Context) -> None:
        state_file_path = self._workspace.get_path(f"{self._thread_id}_state.pkl")
        with open(state_file_path, 'wb') as file:
            pickle.dump(context, file)

    async def load(self) -> Context:
        state = Context()
        state_file_path = self._workspace.get_path(f"{self._thread_id}_state.pkl")
        if state_file_path.exists():
            with open(state_file_path, 'rb') as file:
                state = pickle.load(file)
        return state

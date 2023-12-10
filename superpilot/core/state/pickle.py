import logging
import pickle

from superpilot.core.state.base import BaseState
from superpilot.core.state.mixins import PickleStateMixin
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

    async def save(self, state: dict) -> None:
        state_file_path = self._workspace.get_path(f"{self._thread_id}_state.pkl")
        with open(state_file_path, 'wb') as file:
            pickle.dump(state, file)

    async def load(self, obj: PickleStateMixin) -> dict:
        state = {}
        state_file_path = self._workspace.get_path(f"{self._thread_id}_state.pkl")
        if state_file_path.exists():
            with open(state_file_path, 'rb') as file:
                state = pickle.load(file)
        return state

    @classmethod
    async def load_from_dict(cls, obj: PickleStateMixin, state: dict) -> None:
        if not hasattr(obj, 'from_pickle_state'):
            raise Exception("Implement DictStateMixin")
        await obj.from_pickle_state(state)

    @classmethod
    async def get_dict(cls, obj: PickleStateMixin) -> dict:
        if not hasattr(obj, 'to_pickle_state'):
            raise Exception("Implement DictStateMixin")
        return await obj.to_pickle_state()

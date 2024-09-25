from superpilot.core.store.base import VectorStoreBase
from superpilot.core.store.schema import Object


class VespaStore(VectorStoreBase):
    def get(self, object_id):
        pass

    def get_all(self):
        pass

    def update(self, object_id, data):
        pass

    def delete(self, object_id):
        pass

    def history(self, object_id):
        pass

    def index(self, chunks: list[Object]) -> set[Object]:
        pass

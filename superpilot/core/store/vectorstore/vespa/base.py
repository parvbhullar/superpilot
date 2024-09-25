from superpilot.core.store.base import VectorStoreBase
from superpilot.core.store.schema import Object



class VespaStore(VectorStoreBase):
    def __init__(self):
        self.indexed_data = set()

    def get(self, object_id):
        # Sample implementation for getting an object by id
        for obj in self.indexed_data:
            if obj.obj_id == object_id:
                return obj
        return None

    def get_all(self):
        # Return all indexed objects
        return list(self.indexed_data)

    def index(self, chunks: list[Object]) -> set[Object]:
        """
        Indexes a list of document chunks, ensuring no duplicates.
        """
        for chunk in chunks:
            self.indexed_data.add(chunk)
        return self.indexed_data



'''
    def update(self, object_id, data):
        pass

    def delete(self, object_id):
        pass

    def history(self, object_id):
        pass

    def index(self, chunks: list[Object]) -> set[Object]:
        pass

        '''


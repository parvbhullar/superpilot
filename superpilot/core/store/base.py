from abc import ABC, abstractmethod
from typing import List, Set, Any

from superpilot.core.store.schema import Object
from superpilot.superpilot.core.store.vectorstore.vespa.vespa_base import VespaStore
from superpilot.core.store.interfaces import Indexable


class StoreBase(ABC):
    @abstractmethod
    def get(self, object_id):
        """
        Retrieve a object by ID.

        Args:
            object_id (str): ID of the object to retrieve.

        Returns:
            dict: Retrieved object.
        """
        pass

    @abstractmethod
    def get_all(self):
        """
        List all memories.

        Returns:
            list: List of all memories.
        """
        pass

    @abstractmethod
    def update(self, object_id, data):
        """
        Update a object by ID.

        Args:
            object_id (str): ID of the object to update.
            data (dict): Data to update the object with.

        Returns:
            dict: Updated object.
        """
        pass

    @abstractmethod
    def delete(self, object_id):
        """
        Delete a object by ID.

        Args:
            object_id (str): ID of the object to delete.
        """
        pass

    @abstractmethod
    def history(self, object_id):
        """
        Get the history of changes for a object by ID.

        Args:
            object_id (str): ID of the object to get history for.

        Returns:
            list: List of changes for the object.
        """
        pass


class VectorStoreBase(StoreBase, Indexable,  ABC):

    storebase=StoreBase()
    indexable=Indexable()
    

    

class DBBase(StoreBase):
    pass


class DocumentIndexer(Indexable):
    def create_index(self, **kwargs: Any) -> set[Object]:
        pass

    def index(self, chunks: List[Object]) -> Set[str]:
        """
        Indexes the provided chunks, overwriting existing chunks if necessary.
        """
        document_ids = set()

        for chunk in chunks:
            # Ensure the document gets reindexed (clear existing first)
            if chunk.obj_id in self.primary_index:
                del self.primary_index[chunk.obj_id]  # Clear existing entry

            # Index the new chunk
            self.primary_index[chunk.obj_id] = chunk

            # Add document ID to the set
            document_ids.add(chunk.obj_id)

        return document_ids
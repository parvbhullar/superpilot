from abc import ABC, abstractmethod

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
    pass

class DBBase(StoreBase):
    pass
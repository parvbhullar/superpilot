import enum
from abc import abstractmethod, ABC
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ObjectType(str, enum.Enum):
    # TBD what these actually are.
    TEXT = "text"
    JSON = "json"

class Privacy(str, enum.Enum):
    # TBD what these actually are.
    Public = "public"
    Private = "private"
    Shared = "shared"

class BaseObject(ABC):

    @property
    @abstractmethod
    def type(self) -> ObjectType:
        """Type of the content item"""
        ...

    @property
    @abstractmethod
    def source(self) -> Optional[str]:
        """A string indicating the source location of the content item"""
        ...

    @property
    @abstractmethod
    def content(self) -> str:
        """The content represented by the content item"""
        ...

    def __str__(self) -> str:
        return (
            f"{self.description}, source: {self.source})\n"
            "```\n"
            f"{self.content}\n"
            "```"
        )


class Object(BaseModel):
    """Struct for a message and its metadata."""
    blurb: str  # The first sentence(s) of the first Section of the chunk
    content: str # Content of object
    source: str
    type: ObjectType
    metadata: dict
    ref_id: str
    privacy: Privacy
    embeddings: dict # Embedding of an chunk of text
    timestamp: datetime = datetime.now()
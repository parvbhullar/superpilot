import enum
from abc import abstractmethod, ABC
from datetime import datetime
from typing import Optional, Any

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
    metadata: dict[str, str | list[str]]
    ref_id: str
    obj_id: str
    privacy: Privacy
    embeddings: dict # Embedding of an chunk of text
    timestamp: datetime = datetime.now()



class InferenceObject(Object):
    semantic_identifier: str
    boost: int
    recency_bias: float
    score: float | None
    hidden: bool
    # Matched sections in the chunk. Uses Vespa syntax e.g. <hi>TEXT</hi>
    # to specify that a set of words should be highlighted. For example:
    # ["<hi>the</hi> <hi>answer</hi> is 42", "he couldn't find an <hi>answer</hi>"]
    match_highlights: list[str]
    # when the doc was last updated
    updated_at: datetime | None
    # primary_owners: list[str] | None = None
    # secondary_owners: list[str] | None = None

    @property
    def unique_id(self) -> str:
        return f"{self.ref_id}__{self.obj_id}"

    def __repr__(self) -> str:
        blurb_words = self.blurb.split()
        short_blurb = ""
        for word in blurb_words:
            if not short_blurb:
                short_blurb = word
                continue
            if len(short_blurb) > 25:
                break
            short_blurb += " " + word
        return f"Inference Chunk: {self.ref_id} - {short_blurb}..."

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, InferenceObject):
            return False
        return (self.ref_id, self.obj_id) == (other.ref_id, other.obj_id)

    def __hash__(self) -> int:
        return hash((self.ref_id, self.obj_id))
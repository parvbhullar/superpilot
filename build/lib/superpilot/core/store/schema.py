import enum
from abc import abstractmethod, ABC
from datetime import datetime
from typing import Optional, Any,Dict,List,Set,Union

from pydantic import BaseModel,Field


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
from datetime import datetime

class Object(BaseModel):
    """Struct for a message and its metadata."""
    blurb: str = Field(..., description="The first sentence(s) of the chunk")
    content: str = Field(..., description="Content of object")
    source: str = Field(..., description="Source of the object")
    type: ObjectType = Field(..., description="Type of the object")
    metadata: Dict[str, Union[str, List[str]]] = Field(default_factory=dict, description="Metadata of the object")
    ref_id: str = Field(..., description="Reference ID of the object")
    obj_id: str = Field(..., description="Object ID")
    privacy: Privacy = Field(..., description="Privacy settings of the object")
    embeddings: Dict[str, Any] = Field(default_factory=dict, description="Embeddings of the object text")
    timestamp: Optional[datetime] = datetime.now()


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
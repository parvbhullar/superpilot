from typing import Dict, Type, Any, Optional, List, Union
from pydantic import BaseModel, create_model, root_validator, validator
import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


class ContentType(str, enum.Enum):
    # TBD what these actually are.
    MARKDOWN = "markdown"
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    FOLDER = "folder"
    DICT = "dict"
    LIST = "dict"
    XML = "xml"
    EXCEPTION = "exception"
    CLASS_OBJECT = "class_object"


class ContentItem(ABC):
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the content item"""
        ...

    @property
    @abstractmethod
    def type(self) -> ContentType:
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
            f"{self.description} (source: {self.source}) (type: {self.type})\n"
            "```\n"
            f"{self.content}\n"
            "```"
        )

    def summary(self) -> str:
        return self.__str__()


@dataclass
class FileContentItem(ContentItem):
    file_path: Path
    type = ContentType.FILE

    @property
    def source(self) -> str:
        return f"local file '{self.file_path}'"

    @property
    def content(self) -> str:
        return open(self.file_path).read()

    @property
    def description(self) -> str:
        return f"The contents of the file '{self.file_path}' in the workspace"


@dataclass
class ImageContentItem(ContentItem):
    file_path: Path
    type = ContentType.IMAGE

    @property
    def source(self) -> str:
        return f"local file '{self.file_path}'"

    @property
    def content(self) -> str:
        return "Image content"

    @property
    def description(self) -> str:
        return f"The contents of the file '{self.file_path}' in the workspace"


@dataclass
class FolderContentItem(ContentItem):
    path: Path
    type = ContentType.FOLDER

    def __post_init__(self) -> None:
        assert self.path.exists(), "Selected path does not exist"
        assert self.path.is_dir(), "Selected path is not a directory"

    @property
    def description(self) -> str:
        return f"The contents of the folder '{self.path}' in the workspace"

    @property
    def source(self) -> str:
        return f"local folder '{self.path}'"

    @property
    def content(self) -> str:
        items = [f"{p.name}{'/' if p.is_dir() else ''}" for p in self.path.iterdir()]
        items.sort()
        return "\n".join(items)


@dataclass
class ObjectContent(ContentItem):
    @property
    def source(self) -> Optional[str]:
        return self.obj_source

    @property
    def content(self) -> str:
        return str(self.obj_content)

    @property
    def type(self) -> ContentType:
        return self.obj_type

    obj_content: Union[List, Dict]
    obj_source: Optional[str] = None
    obj_type = ContentType.CLASS_OBJECT

    @property
    def description(self) -> str:
        return f"The is object of '{self.source}'"

    @staticmethod
    def add(content: dict | list, source: str = None):
        knowledge = ObjectContent(content, source)
        knowledge.content_type = (
            isinstance(content, dict) and ContentType.DICT or ContentType.LIST
        )
        return knowledge


class Content(ContentItem):
    @property
    def type(self) -> ContentType:
        return self.content_type

    @property
    def description(self) -> str:
        return f"The content of object of '{self.type}'"

    content: str = ""
    content_type: ContentType = ContentType.TEXT
    source: Optional[str] = None
    content_metadata: Dict[str, Any] = {}
    content_model: BaseModel = str

    @staticmethod
    def add_content_item(
        content: str = None,
        content_type: str = "text",
        source: str = None,
        content_metadata: Dict[str, Any] = {},
    ):
        knowledge = Content()
        knowledge.content = content
        knowledge.content_type = content_type
        knowledge.source = source
        knowledge.content_metadata = content_metadata
        return knowledge

    @classmethod
    def create_model_class(cls, class_name: str, mapping: Dict[str, Type]):
        new_class = create_model(class_name, **mapping)

        @validator("*", allow_reuse=True)
        def check_name(v, field):
            if field.name not in mapping.keys():
                raise ValueError(f"Unrecognized block: {field.name}")
            return v

        @root_validator(pre=True, allow_reuse=True)
        def check_missing_fields(values):
            required_fields = set(mapping.keys())
            missing_fields = required_fields - set(values.keys())
            if missing_fields:
                raise ValueError(f"Missing fields: {missing_fields}")
            return values

        new_class.__validator_check_name = classmethod(check_name)
        new_class.__root_validator_check_missing_fields = classmethod(
            check_missing_fields
        )
        return new_class


class Context:
    items: list[ContentItem]

    def __init__(self, items: list[ContentItem] = None):
        if not items:
            items = []
        self.items = items

    def extend(self, context: "Context") -> None:
        if context:
            self.items.extend(context.items)

    def __bool__(self) -> bool:
        return len(self.items) > 0

    def add(self, item: Any) -> None:
        if isinstance(item, ContentItem):
            self.items.append(item)
        elif isinstance(item, Exception):
            self.items.append(
                Content.add_content_item(str(item), ContentType.EXCEPTION)
            )
        elif isinstance(item, str):
            self.items.append(Content.add_content_item(item, ContentType.TEXT))
        else:
            self.items.append(ObjectContent.add(item))

    def add_content(self, content: str) -> "Context":
        item = Content.add_content_item(content, ContentType.TEXT)
        self.items.append(item)
        return self

    def close(self, index: int) -> None:
        self.items.pop(index - 1)

    def clear(self) -> None:
        self.items.clear()

    def count(self) -> int:
        return len(self.items)

    def format_numbered(self) -> str:
        return "\n\n".join([f"{i}. {c}" for i, c in enumerate(self.items, 1)])

    def __str__(self) -> str:
        return "\n\n".join([f"{c}" for i, c in enumerate(self.items, 1)])

    def dict(self):
        return {"content": self.__str__()}

    def to_list(self):
        return [c for c in self.items]

    def to_file(self, file_location: str) -> None:
        with open(file_location, "w") as f:
            f.write(str(self.format_numbered()))

    @classmethod
    def factory(cls, items: list[ContentItem] = None):
        if items is None:
            items = []
        return cls(items)

import enum
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Type, Any, Optional, List, Union

# from pydantic import field_validator, model_validator, BaseModel, create_model
from pydantic import BaseModel, create_model

from superpilot.core.planning import Task, TaskStatus


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
            f"{self.description}, source: {self.source})\n"
            "```\n"
            f"{self.content}\n"
            "```"
        )

    @property
    def summary(self) -> str:
        # TODO write a function to summarise the content
        return self.content


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
        return open(self.file_path).read()

    @property
    def description(self) -> str:
        return f"The contents of the image '{self.file_path}' in the workspace"


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

        # @field_validator("*")
        @classmethod
        def check_name(v, field):
            if field.name not in mapping.keys():
                raise ValueError(f"Unrecognized block: {field.name}")
            return v

        # @model_validator(mode="before")
        @classmethod
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


class Role(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    SYSTEM = "system"

    def __str__(self):
        return self.value


class Event(str, enum.Enum):
    PLANNING = "planning"
    EXECUTION = "execution"
    LLM_RESPONSE = "llm_response"
    USER_INPUT = "user_input"
    QUESTION = "question"

    def __str__(self):
        return self.value


class User(BaseModel):
    """Struct for metadata about a sender."""
    id: uuid.UUID
    name: str
    role: Role
    additional_data: dict = None

    @property
    def username(self):
        return f"{self.name} ({self.role})"

    @classmethod
    def add_user(cls, name: str = "System", role: Role = Role.SYSTEM, _id: uuid.UUID = uuid.uuid4(), additional_data: dict = None):
        if not additional_data:
            additional_data = {}
        return cls(id=_id, name=name, role=role, additional_data=additional_data)


class MessageContent(BaseModel):
    pass


class Message(BaseModel):
    """Struct for a message and its metadata."""
    sender: User
    message: str
    attachments: list[ContentItem] = []
    additional_data: Any = None
    event: Event = Event.USER_INPUT
    thread_id: str = str(uuid.uuid4())
    timestamp: datetime = datetime.now()

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(
            cls,
            message: str,
            user: User = None,
            event: Event = None,
            attachments: list[ContentItem] = None,
            additional_data: Any = None
    ):
        if not attachments:
            attachments = []
        if not user:
            user = User.add_user()
        return cls(sender=user, message=message, attachments=attachments, event=event, additional_data=additional_data)

    @classmethod
    def add_user_message(cls, message: str, attachments: list[ContentItem] = None, additional_data: Any = None):
        user = User.add_user(name="User", role=Role.USER)
        return cls.create(message, user, Event.USER_INPUT, attachments, additional_data)

    @classmethod
    def add_question_message(cls, message: str, attachments: list[ContentItem] = None, additional_data: Any = None):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.QUESTION, attachments, additional_data)

    @classmethod
    def add_planning_message(cls, message: str, attachments: list[ContentItem] = None, additional_data: Any = None):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.PLANNING, attachments, additional_data)


    @classmethod
    def add_assistant_message(cls, message: str, attachments: list[ContentItem] = None, additional_data: Any = None):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.LLM_RESPONSE, attachments, additional_data)

    @classmethod
    def add_execution_message(cls, message: str, attachments: list[ContentItem] = None, additional_data: Any = None):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.EXECUTION, attachments, additional_data)

    def add_attachment(self, item: Any) -> None:
        if isinstance(item, ContentItem):
            self.attachments.append(item)
        elif isinstance(item, Exception):
            self.attachments.append(
                Content.add_content_item(str(item), ContentType.EXCEPTION)
            )
        elif isinstance(item, str):
            self.attachments.append(Content.add_content_item(item, ContentType.TEXT))
        else:
            self.attachments.append(ObjectContent.add(item))

    def __str__(self) -> str:
        # return "\n\n".join([f"{c}" for i, c in enumerate(self.attachments, 1)])
        summary = "\n\n".join([f"{c.summary}" for i, c in enumerate(self.attachments, 1)])
        return (
            f"[{self.event}] - {self.sender.username}: \n{self.message}\n" +
            (
                "```\n"
                f"{summary}\n"
                "```"
                if summary else ""
            )
        )

    def to_list(self):
        return [c for c in self.attachments]

    def to_file(self, file_location: str) -> None:
        with open(file_location, "w") as f:
            f.write(str(self))

    @property
    def summary(self) -> str:
        return self.__str__()


class Context:
    thread_id: str
    objective: str
    messages: list[Message]

    interaction: bool
    tasks: List[Task]
    active_message: int

    def __init__(self, messages: list[Message] = None):
        if not messages:
            messages = []
        self.messages = messages
        self.tasks = []
        self.interaction = False
        self.active_message = -1
        self.thread_id = ""
        self.objective = ""

    def extend(self, context: "Context") -> None:
        if context:
            self.messages.extend(context.messages)

    def __bool__(self) -> bool:
        return len(self.messages) > 0

    def add_message(self, message: Message):
        self.messages.append(message)

    def add_user_message(self, message: str, attachments: list[ContentItem] = None, additional_data: Any = None):
        message = Message.add_user_message(message, attachments, additional_data)
        self.add_message(message)

    def add_assistant_message(self, message: str, attachments: list[ContentItem] = None, additional_data: Any = None):
        message = Message.add_assistant_message(message, attachments, additional_data)
        self.add_message(message)

    def add_execution_message(self, message: str, attachments: list[ContentItem] = None, additional_data: Any = None):
        message = Message.add_execution_message(message, attachments, additional_data)
        self.add_message(message)

    def add_attachment(self, item: Any, message: str = "Empty") -> None:
        if len(self.messages) == 0:
            self.add_user_message(message)
        self.messages[self.active_message].add_attachment(item)

    def add_content(self, content: str) -> "Context":
        item = Content.add_content_item(content, ContentType.TEXT)
        self.add_attachment(item)
        return self

    def close(self, index: int) -> None:
        self.messages.pop(index - 1)

    def clear(self) -> None:
        self.messages.clear()

    def count(self) -> int:
        return len(self.messages)

    def format_numbered(self) -> str:
        return "\n\n".join([f"{i}. {c}" for i, c in enumerate(self.messages, 1)])

    def __str__(self) -> str:
        return "\n\n".join([f"{c}" for i, c in enumerate(self.messages, 1)])

    def dict(self):
        return {"content": self.__str__()}

    def to_list(self):
        return [c for c in self.messages]

    def to_file(self, file_location: str) -> None:
        with open(file_location, "w") as f:
            f.write(str(self.format_numbered()))

    def summary(self) -> str:
        return "\n\n".join([f"{c.summary}" for i, c in enumerate(self.messages, 1)])

    @classmethod
    def factory(cls, items: list[ContentItem] = None):
        if items is None:
            items = []
        return cls(items)

    @property
    def current_task(self) -> Task:
        if len(self.tasks):
            task = self.tasks[-1]
            if task.status != TaskStatus.DONE:
                return task

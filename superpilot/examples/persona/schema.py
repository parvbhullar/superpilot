import enum
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Type, Any, Optional, List, Union

# from pydantic import field_validator, model_validator, BaseModel, create_model
from pydantic import BaseModel, Field, create_model

from superpilot.core.resource.model_providers import LanguageModelProviderModelResponse


class LanguageModelResponse(LanguageModelProviderModelResponse):
    """Standard response struct for a response from a language model."""


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
    TASK_START = "task_start"
    TASK_END = "task_end"

    def __str__(self):
        return self.value


class User(BaseModel):
    """Struct for metadata about a sender."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: Role
    data: dict = None

    @property
    def username(self):
        return f"{self.name} ({self.role})"

    @classmethod
    def add_user(
        cls,
        name: str = "System",
        role: Role = Role.SYSTEM,
        _id: str = str(uuid.uuid4()),
        data: dict = None,
    ):
        if not data:
            data = {}
        return cls(id=_id, name=name, role=role, data=data)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "data": self.data
        }


class MessageContent(BaseModel):
    pass


class Message(BaseModel):
    """Struct for a message and its metadata."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: User
    message: str
    data: Any = None
    attachments: list[ContentItem] = []
    event: Event = Event.USER_INPUT
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    history: list["Message"] = []

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(
        cls,
        message: str,
        user: User = None,
        event: Event = Event.USER_INPUT,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        if not attachments:
            attachments = []
        if not user:
            user = User.add_user()
        return cls(
            sender=user,
            message=message,
            attachments=attachments,
            event=event,
            data=data,
            **kwargs,
        )

    @classmethod
    def from_model_response(cls, lmr: LanguageModelResponse, session_id= None, user: User = None):
        """Create a Message instance from a LanguageModelResponse object."""
        # Extract the message content from the LanguageModelResponse
        content = lmr.content.pop('content', lmr.content.pop('answer', ""))
        if not user:
            # Assume 'assistant' is a role; adjust as needed
            user = User.add_user(lmr.model_info.model_name, Role.ASSISTANT)
        # Set the event to LANGUAGE_MODEL_RESPONSE or appropriate event
        event = Event.LLM_RESPONSE
        # Use the entire lmr as data
        data = lmr.content
        return cls(sender=user, message=content, event=event, data=data, session_id=session_id)

    @classmethod
    def from_block(cls, block_json: dict, **kwargs):
        """Create a Message instance from a JSON dictionary."""
        message_content = block_json.get("data", {}).get("content", "")
        data = block_json.get("data", {})
        attachments = []

        # files = data.get('files', [])
        # for file_dict in files:
        #     # Assuming ContentItem can be initialized from a dictionary
        #     attachment = ContentItem(**file_dict)
        #     attachments.append(attachment)
        history = []
        for message_dict in data.get('history', []):
            message = Message.from_block(message_dict)
            history.append(message)
        # Include any additional fields from the JSON if necessary
        event = Event.USER_INPUT  # Default event
        user = User.add_user()  # Default user

        return cls.create(
            message=message_content,
            user=user,
            event=event,
            attachments=attachments,
            data=data,
            history=history,
            **kwargs,
        )

    @classmethod
    def from_memory(cls, memory: dict):
        # Example memory:
        # {'id': '8936f00d-cefe-4af4-bc8f-1ddaa0fac182', 'memory': 'Likes to play cricket on weekends',
        #  'hash': '285d07801ae42054732314853e9eadd7', 'metadata': {'category': 'hobbies'}, 'score': 0.09893511,
        #  'created_at': '2024-10-13T04:04:24.526226-07:00', 'updated_at': None, 'user_id': 'session_123'}]
        # message_content = memory.get("memory", "")
        # data = memory.get("metadata", {})
        # attachments = []
        return cls(
            id=memory.get("id", ""),
            **memory.get('metadata')
        )

    @classmethod
    def add_user_message(
        cls,
        message: str,
        attachments: list[ContentItem] = None,
        data: Any = None,
        **kwargs,
    ):
        user = User.add_user(name="User", role=Role.USER)
        return cls.create(
            message, user, Event.USER_INPUT, attachments, data, kwargs=kwargs
        )

    @classmethod
    def add_question_message(
        cls, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.QUESTION, attachments, data)

    @classmethod
    def add_planning_message(
        cls, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.PLANNING, attachments, data)

    @classmethod
    def add_task_start_message(
        cls, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.TASK_START, attachments, data)

    @classmethod
    def add_task_end_message(
        cls, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.TASK_END, attachments, data)

    @classmethod
    def add_assistant_message(
        cls, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.LLM_RESPONSE, attachments, data)

    @classmethod
    def add_execution_message(
        cls, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        user = User.add_user(name="Assistant", role=Role.ASSISTANT)
        return cls.create(message, user, Event.EXECUTION, attachments, data)

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
        summary = "\n\n".join(
            [f"{c.summary}" for i, c in enumerate(self.attachments, 1)]
        )
        return f"[{self.event}] - {self.sender.username}: \n{self.message}\n" + (
            "```\n" f"{summary}\n" "```" if summary else ""
        )

    def to_list(self):
        return [c for c in self.attachments]

    def to_file(self, file_location: str) -> None:
        with open(file_location, "w") as f:
            f.write(str(self))

    @property
    def summary(self) -> str:
        return self.__str__()

    def generate_kwargs(self) -> dict[str, str]:
        return {
            "message": self.message,
            "data": json.dumps(self.data),
            "attachments": [c.summary for c in self.attachments],
            "event": self.event,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }

    def to_memory(self):
        return {
            "memory": str(self),
            "ref_id": self.session_id,
            "metadata": {
                "message": self.message,
                "session_id": self.session_id,
                "data": self.data,
                "attachments": [c.summary for c in self.attachments],
                "event": self.event,
                "sender_id": self.sender.id,
                "sender": self.sender.to_dict(),
                "timestamp": self.timestamp.timestamp(),
            }
        }


class Context:
    session_id: str
    objective: str
    messages: list[Message]

    interaction: bool
    # tasks: List[Task]
    active_message: int

    def __init__(self, session_id, messages: list[Message] = None):
        if not messages:
            messages = []
        self.messages = messages
        self.tasks = []
        self.interaction = False
        self.active_message = -1
        self.session_id = session_id
        self.objective = ""

    def extend(self, context: "Context") -> None:
        if context:
            self.messages.extend(context.messages)

    def __bool__(self) -> bool:
        return len(self.messages) > 0

    def add_message(self, message: Message):
        if len(self.messages) == 0:
            self.objective = message.message
        self.messages.append(message)

    def add_user_message(
        self, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        message = Message.add_user_message(message, attachments, data)
        self.add_message(message)

    def add_assistant_message(
        self, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        message = Message.add_assistant_message(message, attachments, data)
        self.add_message(message)

    def add_execution_message(
        self, message: str, attachments: list[ContentItem] = None, data: Any = None
    ):
        message = Message.add_execution_message(message, attachments, data)
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

    def to_memories(self):
        return [c.to_memory() for c in self.messages]

    def summary(self) -> str:
        return "\n\n".join([f"{c.summary}" for i, c in enumerate(self.messages, 1)])

    def get_last_user_message(self):
        for message in reversed(self.messages):
            if message.sender.role == Role.USER:
                return message
        return None

    @classmethod
    def factory(cls, session_id, messages: list[Message] = None):
        if messages is None:
            items = []
        return cls(messages)

    @classmethod
    def from_memories(cls, session_id, memories: list[dict] = None):
        if memories is None:
            memories = []
        messages = [Message.from_memory(memory) for memory in memories]
        context = cls(session_id, messages)
        context.objective = context.get_last_user_message()
        context.active_message = len(messages) - 1
        return context


    # def current_task(self) -> Task:
    # @property

    #     if len(self.tasks):
    #         task = self.tasks[-1]
    #         if task.status != TaskStatus.DONE:
    #             return task

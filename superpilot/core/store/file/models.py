from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from super_store.configs.constants import DocumentSource
from super_store.configs.constants import INDEX_SEPARATOR
from super_store.utils.text_processing import make_url_compatible


class InputType(str, Enum):
    LOAD_STATE = "load_state"  # e.g. loading a current full state or a save state, such as from a file
    POLL = "poll"  # e.g. calling an API to get all documents in the last hour
    EVENT = "event"  # e.g. registered an endpoint as a listener, and processing connector events
    PRUNE = "prune"


class ConnectorMissingCredentialError(PermissionError):
    def __init__(self, connector_name: str) -> None:
        connector_name = connector_name or "Unknown"
        super().__init__(
            f"{connector_name} connector missing credentials, was load_credentials called?"
        )


class Section(BaseModel):
    text: str
    link: str | None


class BasicExpertInfo(BaseModel):
    """Basic Information for the owner of a document, any of the fields can be left as None
    Display fallback goes as follows:
    - first_name + (optional middle_initial) + last_name
    - display_name
    - email
    - first_name
    """

    display_name: str | None = None
    first_name: str | None = None
    middle_initial: str | None = None
    last_name: str | None = None
    email: str | None = None

    def get_semantic_name(self) -> str:
        if self.first_name and self.last_name:
            name_parts = [self.first_name]
            if self.middle_initial:
                name_parts.append(self.middle_initial + ".")
            name_parts.append(self.last_name)
            return " ".join([name_part.capitalize() for name_part in name_parts])

        if self.display_name:
            return self.display_name

        if self.email:
            return self.email

        if self.first_name:
            return self.first_name.capitalize()

        return "Unknown"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BasicExpertInfo):
            return False
        return (
            self.display_name,
            self.first_name,
            self.middle_initial,
            self.last_name,
            self.email,
        ) == (
            other.display_name,
            other.first_name,
            other.middle_initial,
            other.last_name,
            other.email,
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.display_name,
                self.first_name,
                self.middle_initial,
                self.last_name,
                self.email,
            )
        )


class DocumentBase(BaseModel):
    """Used for Unpod ingestion api, the ID is inferred before use if not provided"""

    id: str | None = None
    sections: list[Section]
    source: DocumentSource | None = None
    semantic_identifier: str  # displayed in the UI as the main identifier for the doc
    metadata: dict[str, str | list[str]]
    # UTC time
    doc_updated_at: datetime | None = None
    # Owner, creator, etc.
    primary_owners: list[BasicExpertInfo] | None = None
    # Assignee, space owner, etc.
    secondary_owners: list[BasicExpertInfo] | None = None
    # title is used for search whereas semantic_identifier is used for displaying in the UI
    # different because Slack message may display as #general but general should not be part
    # of the search, at least not in the same way as a document title should be for like Confluence
    # The default title is semantic_identifier though unless otherwise specified
    title: str | None = None
    from_ingestion_api: bool = False
    hub_id: str | None = None
    kn_token: str | None = None

    def get_title_for_document_index(self) -> str | None:
        # If title is explicitly empty, return a None here for embedding purposes
        if self.title == "":
            return None
        return self.semantic_identifier if self.title is None else self.title

    def get_metadata_str_attributes(self) -> list[str] | None:
        if not self.metadata:
            return None
        # Combined string for the key/value for easy filtering
        attributes: list[str] = []
        for k, v in self.metadata.items():
            if isinstance(v, list):
                attributes.extend([k + INDEX_SEPARATOR + vi for vi in v])
            else:
                attributes.append(k + INDEX_SEPARATOR + v)
        return attributes


class Document(DocumentBase):
    id: str  # This must be unique or during indexing/reindexing, chunks will be overwritten
    source: DocumentSource

    def to_short_descriptor(self) -> str:
        """Used when logging the identity of a document"""
        return f"ID: '{self.id}'; Semantic ID: '{self.semantic_identifier}'"

    @classmethod
    def from_base(cls, base: DocumentBase) -> "Document":
        return cls(
            id=make_url_compatible(base.id)
            if base.id
            else "ingestion_api_" + make_url_compatible(base.semantic_identifier),
            sections=base.sections,
            source=base.source or DocumentSource.INGESTION_API,
            semantic_identifier=base.semantic_identifier,
            metadata=base.metadata,
            doc_updated_at=base.doc_updated_at,
            primary_owners=base.primary_owners,
            secondary_owners=base.secondary_owners,
            title=base.title,
            from_ingestion_api=base.from_ingestion_api,
        )


class IndexAttemptMetadata(BaseModel):
    connector_id: int
    credential_id: int

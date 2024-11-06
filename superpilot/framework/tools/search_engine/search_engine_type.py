from enum import Enum, auto


class SearchEngineType(Enum):
    SERPAPI_GOOGLE = auto()
    DIRECT_GOOGLE = auto()
    SERPER_GOOGLE = auto()
    CUSTOM_ENGINE = auto()
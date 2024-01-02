import abc
import enum
from typing import Callable, ClassVar, List, Union, Any
import json
from functools import wraps
from pydantic import BaseModel, Field, SecretStr, validator, validate_arguments

from superpilot.core.configuration import UserConfigurable
from superpilot.core.resource.schema import (
    Embedding,
    ProviderBudget,
    ProviderCredentials,
    ProviderSettings,
    ProviderUsage,
    ResourceType,
)


class ModelProviderService(str, enum.Enum):
    """A ModelService describes what kind of service the model provides."""

    EMBEDDING: str = "embedding"
    LANGUAGE: str = "language"
    TEXT: str = "text"
    IMAGE: str = "text"
    VIDEO: str = "text"


class ModelProviderName(str, enum.Enum):
    OPENAI: str = "openai"
    ANTHROPIC: str = "anthropic"
    HUGGINGFACE: str = "huggingface"
    OLLAMA: str = "ollama"


class MessageRole(str, enum.Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class MessageContentType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE_URL = "image_url"


class MessageImage(BaseModel):
    url: str
    alt_text: str


class MessageContent(BaseModel):
    type: MessageContentType
    text: str = None
    image_url: MessageImage = None

    def add_image(self, url: str, alt_text: str = ""):
        self.image_url = MessageImage(url=url, alt_text=alt_text)

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        final_data = {}
        for key in d.keys():
            if d[key] is not None and d[key]:
                final_data[key] = d[key]
        return final_data


class LanguageModelMessage(BaseModel):
    role: MessageRole
    content: Union[str, List[MessageContent], None] = None

    # content_list: List[MessageContent] = Field(default_factory=list)

    def add_text(self, text: str):
        # Ensure that content is a list before appending
        if self.content is None or isinstance(self.content, str):
            self.content = []  # Reset content to be a list
        # Append a new MessageContent instance
        # print("Adding TEXT", text)
        self.content.append(MessageContent(type=MessageContentType.TEXT, text=text))

    def add_image(self, url: str, alt_text: str):
        # Ensure that content is a list before appending
        if self.content is None or isinstance(self.content, str):
            self.content = []  # Reset content to be a list

        # print("Adding url", url)
        message = MessageContent(type=MessageContentType.IMAGE_URL, text=alt_text)
        message.add_image(url, alt_text)
        self.content.append(message)

    def to_dict(self):
        return self.dict()

    def __str__(self):
        if self.content is None:
            return "No Content \n" + self.role.value
        if isinstance(self.content, str):
            return (self.content or "") + "\n" + self.role.value
        content = "\n".join([str(c.type) for c in self.content])
        return content + "\n" + self.role.value


class LanguageModelFunction(BaseModel):
    json_schema: dict

    def to_dict(self):
        return self.json_schema

    def __str__(self):
        return json.dumps(self.json_schema, indent=2)


class ModelProviderModelInfo(BaseModel):
    """Struct for model information.

    Would be lovely to eventually get this directly from APIs, but needs to be
    scraped from websites for now.

    """

    name: str
    service: ModelProviderService
    provider_name: ModelProviderName
    prompt_token_cost: float = 0.0
    completion_token_cost: float = 0.0


class ModelProviderModelResponse(BaseModel):
    """Standard response struct for a response from a model."""

    prompt_tokens_used: int
    completion_tokens_used: int
    total_cost: float = 0.0
    model_info: ModelProviderModelInfo


class ModelProviderCredentials(ProviderCredentials):
    """Credentials for a model provider."""

    api_key: Union[SecretStr, None] = UserConfigurable(default=None)
    api_type: Union[SecretStr, None] = UserConfigurable(default=None)
    api_base: Union[SecretStr, None] = UserConfigurable(default=None)
    api_version: Union[SecretStr, None] = UserConfigurable(default=None)
    deployment_id: Union[SecretStr, None] = UserConfigurable(default=None)

    def unmasked(self) -> dict:
        return unmask(self)

    class Config:
        extra = "ignore"


def unmask(model: BaseModel):
    unmasked_fields = {}
    for field_name, field in model.__fields__.items():
        value = getattr(model, field_name)
        if isinstance(value, SecretStr):
            unmasked_fields[field_name] = value.get_secret_value()
        else:
            unmasked_fields[field_name] = value
    return unmasked_fields


class ModelProviderUsage(ProviderUsage):
    """Usage for a particular model from a model provider."""

    completion_tokens: int = 0
    prompt_tokens: int = 0
    total_tokens: int = 0

    def update_usage(
        self,
        model_response: ModelProviderModelResponse,
    ) -> None:
        self.completion_tokens += model_response.completion_tokens_used
        self.prompt_tokens += model_response.prompt_tokens_used
        self.total_tokens += (
            model_response.completion_tokens_used + model_response.prompt_tokens_used
        )


class ModelProviderBudget(ProviderBudget):
    total_budget: float = UserConfigurable()
    total_cost: float = 0
    remaining_budget: float = 0
    usage: ModelProviderUsage

    def update_usage_and_cost(
        self,
        model_response: ModelProviderModelResponse,
    ) -> Any:
        """Update the usage and cost of the provider."""
        model_info = model_response.model_info
        self.usage.update_usage(model_response)
        incremental_cost = (
            model_response.completion_tokens_used * model_info.completion_token_cost
            + model_response.prompt_tokens_used * model_info.prompt_token_cost
        ) / 1000.0
        arb = 0.0055  # TODO: Fit this or get this from the provider
        cost = incremental_cost + arb
        print("Usage", self.usage)
        print("Cost", round(cost, 4))
        self.total_cost += cost
        self.remaining_budget -= cost
        model_response.total_cost = cost
        return self


class ModelProviderSettings(ProviderSettings):
    resource_type = ResourceType.MODEL
    credentials: ModelProviderCredentials
    budget: ModelProviderBudget


class ModelProvider(abc.ABC):
    """A ModelProvider abstracts the details of a particular provider of models."""

    defaults: ClassVar[ModelProviderSettings]

    @abc.abstractmethod
    def get_token_limit(self, model_name: str) -> int:
        ...

    @abc.abstractmethod
    def get_remaining_budget(self) -> float:
        ...

    @abc.abstractmethod
    def get_total_cost(self) -> float:
        ...


####################
# Embedding Models #
####################


class EmbeddingModelProviderModelInfo(ModelProviderModelInfo):
    """Struct for embedding model information."""

    model_service = ModelProviderService.EMBEDDING
    embedding_dimensions: int


class EmbeddingModelProviderModelResponse(ModelProviderModelResponse):
    """Standard response struct for a response from an embedding model."""

    embedding: Embedding = Field(default_factory=list)

    @classmethod
    @validator("completion_tokens_used")
    def _verify_no_completion_tokens_used(cls, v):
        if v > 0:
            raise ValueError("Embeddings should not have completion tokens used.")
        return v


class EmbeddingModelProvider(ModelProvider):
    @abc.abstractmethod
    async def create_embedding(
        self,
        text: str,
        model_name: str,
        embedding_parser: Callable[[Embedding], Embedding],
        **kwargs,
    ) -> EmbeddingModelProviderModelResponse:
        ...


###################
# Language Models #
###################


class LanguageModelProviderModelInfo(ModelProviderModelInfo):
    """Struct for language model information."""

    model_service = ModelProviderService.LANGUAGE
    max_tokens: int


class LanguageModelProviderModelResponse(ModelProviderModelResponse):
    """Standard response struct for a response from a language model."""

    content: dict = None

    def get(self, key, default=None):
        if self.content is None:
            return default
        return self.content.get(key, default)

    def get_content(self):
        return self.content


class LanguageModelProvider(ModelProvider):
    @abc.abstractmethod
    async def create_language_completion(
        self,
        model_prompt: List[LanguageModelMessage],
        functions: List[LanguageModelFunction],
        model_name: str,
        completion_parser: Callable[[dict], dict],
        **kwargs,
    ) -> LanguageModelProviderModelResponse:
        ...


###################
# Media Models #
###################


class MediaModelProviderModelInfo(ModelProviderModelInfo):
    """Struct for language model information."""

    model_service = ModelProviderService.IMAGE
    max_tokens: int


class MediaModelProviderModelResponse(ModelProviderModelResponse):
    """Standard response struct for a response from a language model."""

    content: dict = None


class MediaModelProvider(ModelProvider):
    @abc.abstractmethod
    async def generate(
        self,
        model_prompt: dict,
        model_name: str,
        completion_parser: Callable[[dict], dict],
        **kwargs,
    ) -> MediaModelProviderModelResponse:
        ...


## Function Calls ##
####################
def _remove_a_key(d, remove_key) -> None:
    """Remove a key from a dictionary recursively"""
    if isinstance(d, dict):
        for key in list(d.keys()):
            if key == remove_key:
                del d[key]
            else:
                _remove_a_key(d[key], remove_key)


class schema_function:
    def __init__(self, func: Callable) -> None:
        self.func = func
        self.validate_func = validate_arguments(func)
        parameters = self.validate_func.model.schema()
        parameters["properties"] = {
            k: v
            for k, v in parameters["properties"].items()
            if k not in ("v__duplicate_kwargs", "args", "kwargs")
        }
        parameters["required"] = sorted(
            parameters["properties"]
        )  # bug workaround see lc
        _remove_a_key(parameters, "title")
        _remove_a_key(parameters, "additionalProperties")
        self.openai_schema = {
            "name": self.func.__name__,
            "description": self.func.__doc__,
            "parameters": parameters,
        }
        self.model = self.validate_func.model

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        @wraps(self.func)
        def wrapper(*args, **kwargs):
            return self.validate_func(*args, **kwargs)

        return wrapper(*args, **kwargs)

    def from_response(self, completion, throw_error=True):
        """Execute the function from the response of an openai chat completion"""
        message = completion.choices[0].message
        if throw_error:
            assert "function_call" in message, "No function call detected"
            assert (
                message["function_call"]["name"] == self.openai_schema["name"]
            ), "Function name does not match"

        function_call = message["function_call"]
        arguments = json.loads(function_call["arguments"])
        return self.validate_func(**arguments)


class SchemaModel(BaseModel):
    @classmethod
    def _resolve_ref(cls, ref, definitions):
        # Extract the key from the reference string and return the corresponding definition
        ref_key = ref.split('/')[-1]
        return definitions.get(ref_key)

    @classmethod
    def function_schema(cls, arguments_format=False) -> dict:
        schema = cls.schema()
        definitions = schema.get('definitions', {})

        # Process the properties to replace $ref with actual definitions
        properties = schema.get('properties', {})
        cls.set_properties(definitions, properties)

        # Prepare the final parameters excluding certain keys
        parameters = {k: v for k, v in schema.items() if k not in ("title", "description")}
        parameters["properties"] = properties
        parameters["required"] = sorted(parameters.get("properties", {}))
        # parameters["definitions"] = definitions
        _remove_a_key(parameters, "title")
        if arguments_format:
            name = schema["title"]
            # parameters.pop("required", None)
            # parameters.pop("definitions", None)
            multiple_args = cls.multiple_args()
            if multiple_args:
                return parameters
            parameters['description'] = schema["description"]
            return {
                cls.name(): parameters,
            }
        return {
            "name": schema["title"],
            "description": schema["description"],
            "parameters": parameters,
        }

    @classmethod
    def set_properties(cls, definitions, properties):
        for prop, details in properties.items():
            if 'allOf' in details and len(details['allOf']) == 1 and '$ref' in details['allOf'][0]:
                ref = details['allOf'][0]['$ref']
                resolved_ref = cls._resolve_ref(ref, definitions)
                if resolved_ref:
                    properties[prop] = resolved_ref
                    if resolved_ref.get('type') == 'object':
                        cls.set_properties(definitions, resolved_ref.get('properties', {}))
            if 'type' in details:
                if details['type'] == 'array' and 'items' in details and '$ref' in details['items']:
                    ref = details['items']['$ref']
                    resolved_ref = cls._resolve_ref(ref, definitions)
                    if resolved_ref:
                        properties[prop]['items'] = resolved_ref
                        if resolved_ref.get('type') == 'object':
                            cls.set_properties(definitions, resolved_ref.get('properties', {}))
        return properties

    @classmethod
    def name(cls) -> str:
        schema = cls.schema()
        return schema["title"]

    @classmethod
    def multiple_args(cls) -> bool:
        return False

    @classmethod
    def from_response(cls, completion, throw_error=True):
        message = completion.choices[0].message

        if throw_error:
            assert "function_call" in message, "No function call detected"
            assert (
                message["function_call"]["name"] == cls.function_schema()["name"]
            ), "Function name does not match"

        function_call = message["function_call"]
        arguments = json.loads(function_call["arguments"])
        return cls(**arguments)

import enum
import functools
import logging
import math
import time
import re
from typing import Callable, List, TypeVar, Optional, Any

import anthropic
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from anthropic import APIError, RateLimitError, APIConnectionError, APIStatusError

from superpilot.core.configuration import (
    Configurable,
    SystemConfiguration,
    UserConfigurable,
)
from superpilot.core.resource.model_providers.schema import (
    Embedding,
    EmbeddingModelProvider,
    EmbeddingModelProviderModelInfo,
    EmbeddingModelProviderModelResponse,
    LanguageModelFunction,
    LanguageModelMessage,
    LanguageModelProvider,
    LanguageModelProviderModelInfo,
    LanguageModelProviderModelResponse,
    ModelProviderBudget,
    ModelProviderCredentials,
    ModelProviderName,
    ModelProviderService,
    ModelProviderSettings,
    ModelProviderUsage,
)

AnthropicEmbeddingParser = Callable[[Embedding], Embedding]
AnthropicChatParser = Callable[[str], dict]


class AnthropicModelName(str, enum.Enum):
    CLAUD_2 = "claude-2"
    CLAUD_2_FULL = "claude-2.0"
    CLAUD_2_INSTANT = "claude-instant-1"
    CLAUD_2_INSTANT_FULL = "claude-instant-1.2"


ANTHROPIC_EMBEDDING_MODELS = {
    AnthropicModelName.CLAUD_2: EmbeddingModelProviderModelInfo(
        name=AnthropicModelName.CLAUD_2,
        service=ModelProviderService.EMBEDDING,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.0004,
        completion_token_cost=0.0,
        max_tokens=100000,
        embedding_dimensions=1536,
    ),
}


ANTHROPIC_LANGUAGE_MODELS = {
    AnthropicModelName.CLAUD_2: LanguageModelProviderModelInfo(
        name=AnthropicModelName.CLAUD_2,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.0015,
        completion_token_cost=0.002,
        max_tokens=100000,
    ),
    AnthropicModelName.CLAUD_2_FULL: LanguageModelProviderModelInfo(
        name=AnthropicModelName.CLAUD_2_FULL,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.003,
        completion_token_cost=0.002,
        max_tokens=100000,
    ),
    AnthropicModelName.CLAUD_2_INSTANT: LanguageModelProviderModelInfo(
        name=AnthropicModelName.CLAUD_2_INSTANT,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.03,
        completion_token_cost=0.06,
        max_tokens=100000,
    ),
    AnthropicModelName.CLAUD_2_INSTANT_FULL: LanguageModelProviderModelInfo(
        name=AnthropicModelName.CLAUD_2_INSTANT_FULL,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.06,
        completion_token_cost=0.12,
        max_tokens=100000,
    ),
}


ANTHROPIC_MODELS = {
    **ANTHROPIC_LANGUAGE_MODELS,
    **ANTHROPIC_EMBEDDING_MODELS,
}


class AnthropicConfiguration(SystemConfiguration):
    retries_per_request: int = UserConfigurable()


class AnthropicModelProviderBudget(ModelProviderBudget):
    graceful_shutdown_threshold: float = UserConfigurable()
    warning_threshold: float = UserConfigurable()


class AnthropicSettings(ModelProviderSettings):
    configuration: AnthropicConfiguration
    credentials: ModelProviderCredentials()
    budget: AnthropicModelProviderBudget


class AnthropicApiProvider(
    Configurable,
    LanguageModelProvider,
    EmbeddingModelProvider,
):
    default_settings = AnthropicSettings(
        name="anthropic_provider",
        description="Provides access to Anthropic's API.",
        configuration=AnthropicConfiguration(
            retries_per_request=10,
        ),
        credentials=ModelProviderCredentials(),
        budget=AnthropicModelProviderBudget(
            total_budget=math.inf,
            total_cost=0.0,
            remaining_budget=math.inf,
            usage=ModelProviderUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            ),
            graceful_shutdown_threshold=0.005,
            warning_threshold=0.01,
        ),
    )

    def __init__(
        self,
        settings: AnthropicSettings = default_settings,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        self._budget = settings.budget

        self._logger = logger

        retry_handler = _AnthropicRetryHandler(
            logger=self._logger,
            num_retries=self._configuration.retries_per_request,
        )
        self._client = Anthropic(api_key=self._credentials.api_key)

        self._create_completion = retry_handler(_create_completion)
        # self._create_embedding = retry_handler(_create_embedding) ## TODO: Enable embedding as well.

    def get_token_limit(self, model_name: str) -> int:
        """Get the token limit for a given model."""
        return ANTHROPIC_MODELS[model_name].max_tokens

    def get_remaining_budget(self) -> float:
        """Get the remaining budget."""
        return self._budget.remaining_budget

    def get_total_cost(self) -> float:
        """Get the total cost."""
        return self._budget.total_cost

    async def create_language_completion(
        self,
        model_prompt: List[LanguageModelMessage],
        functions: List[LanguageModelFunction],
        model_name: AnthropicModelName,
        completion_parser: Callable[[dict], dict],
        **kwargs,
    ) -> LanguageModelProviderModelResponse:
        """Create a completion using the Anthropic API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=model_prompt,
            client=self._client,
            **completion_kwargs,
        )
        response_args = {
            "model_info": ANTHROPIC_LANGUAGE_MODELS[model_name],
            "prompt_tokens_used": self._client.count_tokens(self.combine_text_from_objects(model_prompt, functions)),
            "completion_tokens_used": self._client.count_tokens(response.completion),
        }

        parsed_response = completion_parser(
            response.dict()
        )
        response = LanguageModelProviderModelResponse(
            content=parsed_response, **response_args
        )
        self._budget.update_usage_and_cost(response)
        return response

    def combine_text_from_objects(self, model_prompt, functions):
        combined_text = ""

        # Assuming each object in model_prompt has a 'text' attribute
        for message in model_prompt:
            combined_text += str(message) + "\n"

        # Assuming each object in functions has a 'text' attribute
        for function in functions:
            combined_text += str(function) + "\n"

        return combined_text

    async def create_embedding(
        self,
        text: str,
        model_name: AnthropicModelName,
        embedding_parser: Callable[[Embedding], Embedding],
        **kwargs,
    ) -> EmbeddingModelProviderModelResponse:
        """Create an embedding using the Anthropic API."""
        embedding_kwargs = self._get_embedding_kwargs(model_name, **kwargs)
        response = await self._create_embedding(text=text, **embedding_kwargs)

        response_args = {
            "model_info": ANTHROPIC_EMBEDDING_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }
        response = EmbeddingModelProviderModelResponse(
            **response_args,
            embedding=embedding_parser(response.embeddings[0]),
        )
        self._budget.update_usage_and_cost(response)
        return response

    def _get_completion_kwargs(
        self,
        model_name: AnthropicModelName,
        functions: List[LanguageModelFunction],
        **kwargs,
    ) -> dict:
        """Get kwargs for completion API call.

        Args:
            model: The model to use.
            kwargs: Keyword arguments to override the default values.

        Returns:
            The kwargs for the chat API call.

        """
        completion_kwargs = {
            "model": model_name,
            **kwargs,
            # **self._credentials.unmasked(),
            # "request_timeout": 120,
        }
        if functions:
            completion_kwargs["functions"] = functions

        return completion_kwargs

    def _get_embedding_kwargs(
        self,
        model_name: AnthropicModelName,
        **kwargs,
    ) -> dict:
        """Get kwargs for embedding API call.

        Args:
            model: The model to use.
            kwargs: Keyword arguments to override the default values.

        Returns:
            The kwargs for the embedding API call.

        """
        embedding_kwargs = {
            "model": model_name,
            **kwargs,
            # **self._credentials.unmasked(),
        }

        return embedding_kwargs

    def _wrap_prompt(self, prompt: str, **kwargs: Any) -> str:
        if not HUMAN_PROMPT or not AI_PROMPT:
            raise NameError("Please ensure the anthropic package is loaded")

        if prompt.startswith(HUMAN_PROMPT):
            return prompt  # Already wrapped.

        # Guard against common errors in specifying wrong number of newlines.
        corrected_prompt, n_subs = re.subn(r"^\n*Human:", HUMAN_PROMPT, prompt)
        if n_subs == 1:
            return corrected_prompt

        # As a last resort, wrap the prompt ourselves to emulate instruct-style.
        return f"{HUMAN_PROMPT} {prompt}{AI_PROMPT} Sure, here you go:\n"

    def __repr__(self):
        return "AnthropicProvider()"

    @classmethod
    def factory(
        cls,
        api_key: Optional[str] = None,
        retries_per_request: int = 10,
        total_budget: float = float("inf"),
        graceful_shutdown_threshold: float = 0.005,
        warning_threshold: float = 0.01,
        logger: Optional[logging.Logger] = None,
    ) -> "AnthropicApiProvider":
        # Configure logger
        if logger is None:
            logger = logging.getLogger(__name__)

        settings = cls.init_settings(
            api_key,
            retries_per_request,
            total_budget,
            graceful_shutdown_threshold,
            warning_threshold,
        )

        # Instantiate and return AnthropicProvider
        return AnthropicApiProvider(settings=settings, logger=logger)

    @classmethod
    def init_settings(
        cls,
        api_key: Optional[str] = None,
        retries_per_request: int = 10,
        total_budget: float = float("inf"),
        graceful_shutdown_threshold: float = 0.005,
        warning_threshold: float = 0.01,
    ):
        # Initialize settings
        settings = cls.default_settings
        settings.configuration.retries_per_request = retries_per_request
        settings.credentials.api_key = api_key or settings.credentials.api_key
        settings.budget.total_budget = total_budget
        settings.budget.graceful_shutdown_threshold = graceful_shutdown_threshold
        settings.budget.warning_threshold = warning_threshold
        settings = cls.build_configuration(settings.dict())
        return settings


async def _create_embedding(text: str, *_, **kwargs):
    """Embed text using the Anthropic API.

    Args:
        text str: The text to embed.
        model_name str: The name of the model to use.

    Returns:
        str: The embedding.
    """
    return await anthropic.Embedding.acreate(
        input=[text],
        **kwargs,
    )


async def _create_completion(
    messages: List[LanguageModelMessage], client: Anthropic, *_, **kwargs
) -> anthropic.types.Completion:
    """Create a chat completion using the Anthropic API.

    Args:
        messages: The prompt to use.

    Returns:
        The completion.

    """
    prompt = "\n".join([message.__str__() for message in messages])
    if "functions" in kwargs:
        kwargs["functions"] = [function.json_schema for function in kwargs["functions"]]
    else:
        del kwargs["function_call"]
    if "function_call" in kwargs:
        del kwargs["function_call"]
    if "functions" in kwargs:
        del kwargs["functions"]
    # del kwargs["api_type"]
    # del kwargs["api_base"]
    # del kwargs["api_version"]
    # del kwargs["deployment_id"]
    # del kwargs["request_timeout"]
    # anthropic_api_key = kwargs.pop("api_key")

    res = client.completions.create(
        prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
        max_tokens_to_sample=1000,
        **kwargs,
    )
    return res


_T = TypeVar("_T")
# _P = TypeVar("_P")


class _AnthropicRetryHandler:
    """Retry Handler for Anthropic API call.

    Args:
        num_retries int: Number of retries. Defaults to 10.
        backoff_base float: Base for exponential backoff. Defaults to 2.
        warn_user bool: Whether to warn the user. Defaults to True.
    """

    _retry_limit_msg = "Error: Reached rate limit, passing..."
    _api_key_error_msg = (
        "Please double check that you have setup a PAID Anthropic API Account. You can "
        "read more here: https://docs.agpt.co/setup/#getting-an-api-key"
    )
    _backoff_msg = "Error: API Bad gateway. Waiting {backoff} seconds..."

    def __init__(
        self,
        logger: logging.Logger,
        num_retries: int = 10,
        backoff_base: float = 2.0,
        warn_user: bool = True,
    ):
        self._logger = logger
        self._num_retries = num_retries
        self._backoff_base = backoff_base
        self._warn_user = warn_user

    def _log_rate_limit_error(self) -> None:
        self._logger.debug(self._retry_limit_msg)
        if self._warn_user:
            self._logger.warning(self._api_key_error_msg)
            self._warn_user = False

    def _backoff(self, attempt: int) -> None:
        backoff = self._backoff_base ** (attempt + 2)
        self._logger.debug(self._backoff_msg.format(backoff=backoff))
        time.sleep(backoff)

    def __call__(self, func):
        @functools.wraps(func)
        async def _wrapped(*args, **kwargs) -> _T:
            num_attempts = self._num_retries + 1  # +1 for the first attempt
            for attempt in range(1, num_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except RateLimitError:
                    if attempt == num_attempts:
                        raise
                    self._log_rate_limit_error()

                except APIStatusError as e:
                    if (e.status_code != 502) or (attempt == num_attempts):
                        raise

                self._backoff(attempt)

        return _wrapped

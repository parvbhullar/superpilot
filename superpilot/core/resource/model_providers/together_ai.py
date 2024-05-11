import enum
import functools
import logging
import math
import os
import time
from typing import Callable, List, TypeVar, Optional

import together
from together.error import RateLimitError

from superpilot.core.configuration import (
    Configurable,
    SystemConfiguration,
    UserConfigurable,
)
from superpilot.core.resource.model_providers.schema import (
    Embedding,
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

TogetherAIEmbeddingParser = Callable[[Embedding], Embedding]
TogetherAIChatParser = Callable[[str], dict]


class TogetherAIModelName(str, enum.Enum):
    META_LLAMA_3_8B_CHAT_HF = "meta-llama/Llama-3-8b-chat-hf"
    TOGETHER_LLAMA_2_7B_32K_INSTRUCT = "togethercomputer/Llama-2-7B-32K-Instruct"


TOGETHER_AI_EMBEDDING_MODELS = {}


TOGETHER_AI_LANGUAGE_MODELS = {
    TogetherAIModelName.TOGETHER_LLAMA_2_7B_32K_INSTRUCT: LanguageModelProviderModelInfo(
        name=TogetherAIModelName.TOGETHER_LLAMA_2_7B_32K_INSTRUCT,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.TOGETHER,
        prompt_token_cost=0.0004,
        completion_token_cost=0.0,
        max_tokens=32768,
    ),
    TogetherAIModelName.META_LLAMA_3_8B_CHAT_HF: LanguageModelProviderModelInfo(
        name=TogetherAIModelName.META_LLAMA_3_8B_CHAT_HF,
        service=ModelProviderService.EMBEDDING,
        provider_name=ModelProviderName.TOGETHER,
        prompt_token_cost=0.0004,
        completion_token_cost=0.0,
        max_tokens=8000,
    ),
}


TOGETHER_AI_MODELS = {
    **TOGETHER_AI_LANGUAGE_MODELS,
    **TOGETHER_AI_EMBEDDING_MODELS,
}


class TogetherAIConfiguration(SystemConfiguration):
    retries_per_request: int = UserConfigurable()


class TogetherAIModelProviderBudget(ModelProviderBudget):
    graceful_shutdown_threshold: float = UserConfigurable()
    warning_threshold: float = UserConfigurable()


class TogetherAISettings(ModelProviderSettings):
    configuration: TogetherAIConfiguration
    credentials: ModelProviderCredentials()
    budget: TogetherAIModelProviderBudget


class TogetherAIProvider(Configurable, LanguageModelProvider):
    default_settings = TogetherAISettings(
        name="together_provider",
        description="Provides access to TogetherAI's API.",
        configuration=TogetherAIConfiguration(
            retries_per_request=10,
        ),
        credentials=ModelProviderCredentials(
            api_key=os.environ.get("TOGETHER_API_KEY", "")
        ),
        budget=TogetherAIModelProviderBudget(
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
        settings: TogetherAISettings = default_settings,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        self._budget = settings.budget

        self._logger = logger

        retry_handler = _TogetherAIRetryHandler(
            logger=self._logger,
            num_retries=self._configuration.retries_per_request,
        )
        self._client = together.AsyncTogether(
            api_key=self._credentials.api_key.get_secret_value()
        )
        self._create_completion = retry_handler(_create_completion)

    def get_token_limit(self, model_name: str) -> int:
        """Get the token limit for a given model."""
        return TOGETHER_AI_MODELS[model_name].max_tokens

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
        model_name: TogetherAIModelName,
        completion_parser: Callable[[dict], dict],
        **kwargs,
    ) -> LanguageModelProviderModelResponse:
        """Create a completion using the TogetherAI API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=model_prompt,
            client=self._client,
            **completion_kwargs,
        )
        response_args = {
            "model_info": TOGETHER_AI_LANGUAGE_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }

        parsed_response = completion_parser(response.choices[0].message.dict())
        response = LanguageModelProviderModelResponse(
            content=parsed_response, **response_args
        )
        self._budget.update_usage_and_cost(response)
        return response

    async def create_image(
        self,
        model_prompt: List[LanguageModelMessage],
        functions: List[LanguageModelFunction],
        model_name: TogetherAIModelName,
        completion_parser: Callable[[dict], dict],
        **kwargs,
    ) -> LanguageModelProviderModelResponse:
        """Create a completion using the TogetherAI API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=model_prompt,
            **completion_kwargs,
        )
        response_args = {
            "model_info": TOGETHER_AI_LANGUAGE_MODELS[model_name],
            "prompt_tokens_used": response.usage.prompt_tokens,
            "completion_tokens_used": response.usage.completion_tokens,
        }

        parsed_response = completion_parser(
            response.choices[0].message.to_dict_recursive()
        )
        response = LanguageModelProviderModelResponse(
            content=parsed_response, **response_args
        )
        self._budget.update_usage_and_cost(response)
        return response

    def _get_completion_kwargs(
        self,
        model_name: TogetherAIModelName,
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
        completion_kwargs = {"model": model_name}
        return completion_kwargs

    def _get_embedding_kwargs(
        self,
        model_name: TogetherAIModelName,
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
            **self._credentials.unmasked(),
        }

        return embedding_kwargs

    def __repr__(self):
        return "TogetherAIProvider()"

    @classmethod
    def factory(
        cls,
        api_key: Optional[str] = None,
        retries_per_request: int = 10,
        total_budget: float = float("inf"),
        graceful_shutdown_threshold: float = 0.005,
        warning_threshold: float = 0.01,
        logger: Optional[logging.Logger] = None,
    ) -> "TogetherAIProvider":
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

        # Instantiate and return TogetherAIProvider
        return TogetherAIProvider(settings=settings, logger=logger)

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


async def _create_completion(
    messages: List[LanguageModelMessage], client: together.AsyncTogether, *_, **kwargs
) -> together.AsyncComplete:
    """Create a chat completion using the TogetherAI API.

    Args:
        messages: The prompt to use.

    Returns:
        The completion.

    """
    messages = [message.dict() for message in messages]
    # if "functions" in kwargs:
    #     kwargs["functions"] = [function.json_schema for function in kwargs["functions"]]
    # else:
    #     del kwargs["function_call"]
    # # print(messages)
    kwargs.pop("functions", None)
    kwargs.pop("function_call", None)
    return await client.chat.completions.create(
        messages=messages,
        **kwargs,
    )


_T = TypeVar("_T")
# _P = TypeVar("_P")


class _TogetherAIRetryHandler:
    """Retry Handler for TogetherAI API call.

    Args:
        num_retries int: Number of retries. Defaults to 10.
        backoff_base float: Base for exponential backoff. Defaults to 2.
        warn_user bool: Whether to warn the user. Defaults to True.
    """

    _retry_limit_msg = "Error: Reached rate limit, passing..."
    _api_key_error_msg = (
        "Please double check that you have setup a PAID TogetherAI API Account. You can "
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

                except Exception as e:
                    print(e, "Exception in Together API Call")
                    if (e.http_status != 502) or (attempt == num_attempts):
                        raise

                self._backoff(attempt)

        return _wrapped

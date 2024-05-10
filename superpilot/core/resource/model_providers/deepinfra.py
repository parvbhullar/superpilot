import enum
import functools
import logging
import math
import time
from typing import Callable, List, TypeVar, Optional

import openai
from openai.error import APIError, RateLimitError

from superpilot.core.configuration import (
    Configurable,
    SystemConfiguration,
    UserConfigurable,
)
from superpilot.core.resource.model_providers.schema import (
    Embedding,
    EmbeddingModelProvider,
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

DeepInfraEmbeddingParser = Callable[[Embedding], Embedding]
DeepInfraChatParser = Callable[[str], dict]


class DeepInfraModelName(str, enum.Enum):
    OPENCHAT_3_5 = "openchat/openchat_3.5"
    WIZARD_LM_8_22B = "microsoft/WizardLM-2-8x22B"


DEEP_INFRA_EMBEDDING_MODELS = {}


DEEP_INFRA_LANGUAGE_MODELS = {
    DeepInfraModelName.OPENCHAT_3_5: LanguageModelProviderModelInfo(
        name=DeepInfraModelName.OPENCHAT_3_5,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.DEEPINFRA,
        prompt_token_cost=0.003,
        completion_token_cost=0.002,
        max_tokens=8132,
    ),
    DeepInfraModelName.WIZARD_LM_8_22B: LanguageModelProviderModelInfo(
        name=DeepInfraModelName.WIZARD_LM_8_22B,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.DEEPINFRA,
        prompt_token_cost=0.650,
        completion_token_cost=0.650,
        max_tokens=65536,
    ),
}


DEEP_INFRA_MODELS = {
    **DEEP_INFRA_LANGUAGE_MODELS,
    **DEEP_INFRA_EMBEDDING_MODELS,
}


class DeepInfraConfiguration(SystemConfiguration):
    retries_per_request: int = UserConfigurable()


class DeepInfraModelProviderBudget(ModelProviderBudget):
    graceful_shutdown_threshold: float = UserConfigurable()
    warning_threshold: float = UserConfigurable()


class DeepInfraSettings(ModelProviderSettings):
    configuration: DeepInfraConfiguration
    credentials: ModelProviderCredentials()
    budget: DeepInfraModelProviderBudget


class DeepInfraProvider(
    Configurable,
    LanguageModelProvider,
    EmbeddingModelProvider,
):
    default_settings = DeepInfraSettings(
        name="deepinfra_provider",
        description="Provides access to DeepInfra's API.",
        configuration=DeepInfraConfiguration(
            retries_per_request=10,
        ),
        credentials=ModelProviderCredentials(),
        budget=DeepInfraModelProviderBudget(
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
        settings: DeepInfraSettings = default_settings,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        self._budget = settings.budget

        self._logger = logger

        retry_handler = _DeepInfraRetryHandler(
            logger=self._logger,
            num_retries=self._configuration.retries_per_request,
        )
        self._create_completion = retry_handler(_create_completion)
        self._create_embedding = retry_handler(_create_embedding)

    def get_token_limit(self, model_name: str) -> int:
        """Get the token limit for a given model."""
        return DEEP_INFRA_MODELS[model_name].max_tokens

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
        model_name: DeepInfraModelName,
        completion_parser: Callable[[dict], dict],
        **kwargs,
    ) -> LanguageModelProviderModelResponse:
        """Create a completion using the DeepInfra API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=model_prompt,
            **completion_kwargs,
        )
        response_args = {
            "model_info": DEEP_INFRA_LANGUAGE_MODELS[model_name],
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

    async def create_image(
        self,
        model_prompt: List[LanguageModelMessage],
        functions: List[LanguageModelFunction],
        model_name: DeepInfraModelName,
        completion_parser: Callable[[dict], dict],
        **kwargs,
    ) -> LanguageModelProviderModelResponse:
        """Create a completion using the DeepInfra API."""
        completion_kwargs = self._get_completion_kwargs(model_name, functions, **kwargs)
        response = await self._create_completion(
            messages=model_prompt,
            **completion_kwargs,
        )
        response_args = {
            "model_info": DEEP_INFRA_LANGUAGE_MODELS[model_name],
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

    async def create_embedding(
        self,
        text: str,
        model_name: DeepInfraModelName,
        embedding_parser: Callable[[Embedding], Embedding],
        **kwargs,
    ) -> EmbeddingModelProviderModelResponse:
        """Create an embedding using the DeepInfra API."""
        embedding_kwargs = self._get_embedding_kwargs(model_name, **kwargs)
        response = await self._create_embedding(text=text, **embedding_kwargs)

        response_args = {
            "model_info": DEEP_INFRA_EMBEDDING_MODELS[model_name],
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
        model_name: DeepInfraModelName,
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
            **self._credentials.unmasked(),
            "request_timeout": 300,
            "api_base": "https://api.deepinfra.com/v1/openai",
        }
        completion_kwargs["max_tokens"] = self.get_token_limit(model_name)
        if functions:
            completion_kwargs["functions"] = functions

        return completion_kwargs

    def _get_embedding_kwargs(
        self,
        model_name: DeepInfraModelName,
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
        return "DeepInfraProvider()"

    @classmethod
    def factory(
        cls,
        api_key: Optional[str] = None,
        retries_per_request: int = 10,
        total_budget: float = float("inf"),
        graceful_shutdown_threshold: float = 0.005,
        warning_threshold: float = 0.01,
        logger: Optional[logging.Logger] = None,
    ) -> "DeepInfraProvider":
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

        # Instantiate and return DeepInfraProvider
        return DeepInfraProvider(settings=settings, logger=logger)

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


async def _create_embedding(text: str, *_, **kwargs) -> openai.Embedding:
    """Embed text using the DeepInfra API.

    Args:
        text str: The text to embed.
        model_name str: The name of the model to use.

    Returns:
        str: The embedding.
    """
    return await openai.Embedding.acreate(
        input=[text],
        **kwargs,
    )


async def _create_completion(
    messages: List[LanguageModelMessage], *_, **kwargs
) -> openai.Completion:
    """Create a chat completion using the DeepInfra API.

    Args:
        messages: The prompt to use.

    Returns:
        The completion.

    """
    messages = [message.dict() for message in messages]
    if "functions" in kwargs:
        kwargs["functions"] = [function.json_schema for function in kwargs["functions"]]
    else:
        del kwargs["function_call"]
    # print(messages)
    return await openai.ChatCompletion.acreate(
        messages=messages,
        **kwargs,
    )


_T = TypeVar("_T")
# _P = TypeVar("_P")


class _DeepInfraRetryHandler:
    """Retry Handler for DeepInfra API call.

    Args:
        num_retries int: Number of retries. Defaults to 10.
        backoff_base float: Base for exponential backoff. Defaults to 2.
        warn_user bool: Whether to warn the user. Defaults to True.
    """

    _retry_limit_msg = "Error: Reached rate limit, passing..."
    _api_key_error_msg = (
        "Please double check that you have setup a PAID DeepInfra API Account. You can "
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

                except APIError as e:
                    if (e.http_status != 502) or (attempt == num_attempts):
                        raise

                self._backoff(attempt)

        return _wrapped

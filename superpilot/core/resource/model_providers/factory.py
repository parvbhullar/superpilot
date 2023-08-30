import logging
from typing import Optional
from .openai import OpenAIProvider, OpenAISettings, OpenAIConfiguration, OpenAIModelProviderBudget, ModelProviderCredentials


class OpenAIProviderFactory:

    @classmethod
    def create_provider(
            cls,
            retries_per_request: int = 10,
            api_key: Optional[str] = None,
            total_budget: float = float("inf"),
            graceful_shutdown_threshold: float = 0.005,
            warning_threshold: float = 0.01,
            logger: Optional[logging.Logger] = None
    ) -> OpenAIProvider:
        # Configure logger
        if logger is None:
            logger = logging.getLogger(__name__)

        # Initialize settings
        settings = OpenAISettings(
            configuration=OpenAIConfiguration(retries_per_request=retries_per_request),
            credentials=ModelProviderCredentials(api_key=api_key),
            budget=OpenAIModelProviderBudget(
                total_budget=total_budget,
                graceful_shutdown_threshold=graceful_shutdown_threshold,
                warning_threshold=warning_threshold,
            ),
        )

        # Instantiate and return OpenAIProvider
        return OpenAIProvider(settings=settings, logger=logger)


if __name__ == "__main__":
    # Example usage
    factory = OpenAIProviderFactory()
    provider = factory.create_provider(api_key="your_api_key_here")

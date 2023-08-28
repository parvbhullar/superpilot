import logging
import platform
import time
from typing import Dict, List

import distro

from superpilot.core.configuration import Configurable
from superpilot.core.planning import strategies
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import (
    LanguageModelClassification,
    LanguageModelResponse,
    Task,
)
from superpilot.core.planning.settings import (
    PlannerConfiguration,
    PlannerSettings,
    LanguageModelConfiguration,
    PromptStrategiesConfiguration,
)
from superpilot.core.resource.model_providers import (
    LanguageModelProvider,
    ModelProviderName,
    OpenAIModelName,
)
from superpilot.core.workspace import Workspace


class ResearchPlanner(Configurable):
    """Manages the pilot's planning and goal-setting by constructing language model prompts."""

    default_settings = PlannerSettings(
        name="planner",
        description="Manages the pilot's planning and goal-setting by constructing language model prompts.",
        configuration=PlannerConfiguration(
            models={
                LanguageModelClassification.FAST_MODEL: LanguageModelConfiguration(
                    model_name=OpenAIModelName.GPT3,
                    provider_name=ModelProviderName.OPENAI,
                    temperature=0.9,
                ),
                LanguageModelClassification.SMART_MODEL: LanguageModelConfiguration(
                    model_name=OpenAIModelName.GPT4,
                    provider_name=ModelProviderName.OPENAI,
                    temperature=0.9,
                ),
            },
            prompt_strategies=PromptStrategiesConfiguration(
                name_and_goals=strategies.NameAndGoals.default_configuration,
                initial_plan=strategies.InitialPlan.default_configuration,
                next_ability=strategies.NextAbility.default_configuration,
            ),
        ),
    )

    def __init__(
        self,
        settings: PlannerSettings,
        logger: logging.Logger,
        model_providers: Dict[ModelProviderName, LanguageModelProvider],
        workspace: Workspace = None,  # Workspace is not available during bootstrapping.
    ) -> None:
        self._configuration = settings.configuration
        self._logger = logger
        self._workspace = workspace

        self._providers: Dict[LanguageModelClassification, LanguageModelProvider] = {}
        for model, model_config in self._configuration.models.items():
            self._providers[model] = model_providers[model_config.provider_name]

        self._prompt_strategies = {
            "name_and_goals": strategies.NameAndGoals(
                **self._configuration.prompt_strategies.name_and_goals.dict()
            ),
            "initial_plan": strategies.InitialPlan(
                **self._configuration.prompt_strategies.initial_plan.dict()
            ),
            "next_ability": strategies.NextAbility(
                **self._configuration.prompt_strategies.next_ability.dict()
            ),
        }

    async def decide_name_and_goals(self, user_objective: str) -> LanguageModelResponse:
        return await self.chat_with_model(
            self._prompt_strategies["name_and_goals"],
            user_objective=user_objective,
        )

    async def make_initial_plan(
        self,
        pilot_name: str,
        pilot_role: str,
        pilot_goals: List[str],
        abilities: List[str],
    ) -> LanguageModelResponse:
        return await self.chat_with_model(
            self._prompt_strategies["initial_plan"],
            pilot_name=pilot_name,
            pilot_role=pilot_role,
            pilot_goals=pilot_goals,
            abilities=abilities,
        )

    async def determine_next_ability(
        self,
        task: Task,
        ability_schema: List[dict],
    ):
        return await self.chat_with_model(
            self._prompt_strategies["next_ability"],
            task=task,
            ability_schema=ability_schema,
        )

    async def chat_with_model(
        self,
        prompt_strategy: PromptStrategy,
        **kwargs,
    ) -> LanguageModelResponse:
        model_classification = prompt_strategy.model_classification
        model_configuration = self._configuration.models[model_classification].dict()
        self._logger.debug(f"Using model configuration: {model_configuration}")
        del model_configuration["provider_name"]
        provider = self._providers[model_classification]

        template_kwargs = self._make_template_kwargs_for_strategy(prompt_strategy)
        template_kwargs.update(kwargs)
        prompt = prompt_strategy.build_prompt(**template_kwargs)

        self._logger.debug(f"Using prompt:\n{prompt}\n\n")
        response = await provider.create_language_completion(
            model_prompt=prompt.messages,
            functions=prompt.functions,
            **model_configuration,
            completion_parser=prompt_strategy.parse_response_content,
        )
        return LanguageModelResponse.parse_obj(response.dict())

    def _make_template_kwargs_for_strategy(self, strategy: PromptStrategy):
        provider = self._providers[strategy.model_classification]
        template_kwargs = {
            "os_info": get_os_info(),
            "api_budget": provider.get_remaining_budget(),
            "current_time": time.strftime("%c"),
        }
        return template_kwargs


def get_os_info() -> str:
    os_name = platform.system()
    os_info = (
        platform.platform(terse=True)
        if os_name != "Linux"
        else distro.name(pretty=True)
    )
    return os_info

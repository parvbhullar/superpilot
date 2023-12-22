from typing import Dict
from superpilot.core.configuration.schema import (
    SystemConfiguration,
    SystemSettings,
    UserConfigurable,
)
from superpilot.core.planning import strategies
from superpilot.core.planning.schema import LanguageModelClassification
from superpilot.core.resource.model_providers.schema import ModelProviderName


class LanguageModelConfiguration(SystemConfiguration):
    """Struct for model configuration."""

    model_name: str = UserConfigurable()
    provider_name: ModelProviderName = UserConfigurable()
    temperature: float = UserConfigurable()


class PromptStrategyConfiguration(SystemConfiguration):
    model_classification: LanguageModelClassification = UserConfigurable()
    system_prompt: str = UserConfigurable()
    user_prompt_template: str = UserConfigurable()
    parser_schema: dict = None
    location: dict = None


class PromptStrategiesConfiguration(SystemConfiguration):
    name_and_goals: strategies.NameAndGoalsConfiguration = None
    initial_plan: strategies.InitialPlanConfiguration = None
    next_ability: strategies.NextAbilityConfiguration = None
    summarizer: strategies.SummarizerConfiguration = None
    step_execution: strategies.StepExecutionConfiguration = None
    step_response: strategies.StepStrategyConfiguration = None


class PlannerConfigurationLegacy(SystemConfiguration):
    """Configuration for the Planner subsystem."""

    models: Dict[LanguageModelClassification, LanguageModelConfiguration]
    prompt_strategies: PromptStrategiesConfiguration


class PlannerSettingsLegacy(SystemSettings):
    """Settings for the Planner subsystem."""

    configuration: PlannerConfigurationLegacy


class PlannerConfiguration(SystemConfiguration):
    """Configuration for the Planner subsystem."""

    models: Dict[LanguageModelClassification, LanguageModelConfiguration]
    planning_strategy: PromptStrategyConfiguration
    execution_strategy: strategies.NextAbilityConfiguration
    reflection_strategy: PromptStrategyConfiguration


class PlannerSettings(SystemSettings):
    """Settings for the Planner subsystem."""

    configuration: PlannerConfiguration

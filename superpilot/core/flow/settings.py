from typing import Dict

from superpilot.core.configuration.schema import SystemConfiguration
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import StepExecutionNature
from superpilot.core.planning.settings import (
    LanguageModelConfiguration, PromptStrategiesConfiguration, LanguageModelClassification
)


class TaskPilotConfiguration(SystemConfiguration):
    """Struct for model configuration."""

    from superpilot.core.plugin.base import PluginLocation
    location: PluginLocation
    models: Dict[LanguageModelClassification, LanguageModelConfiguration]
    execution_nature: StepExecutionNature = StepExecutionNature.SINGLE
    prompt_strategies: PromptStrategiesConfiguration
    memory_provider_required: bool = False
    workspace_required: bool = False

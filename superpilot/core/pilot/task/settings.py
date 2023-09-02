from typing import Dict

from superpilot.core.configuration.schema import SystemConfiguration
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.schema import ExecutionNature
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    PromptStrategiesConfiguration,
    LanguageModelClassification,
)
from superpilot.core.planning import strategies


class TaskPilotConfiguration(SystemConfiguration):
    """Struct for model configuration."""

    from superpilot.core.plugin.base import PluginLocation
    location: PluginLocation
    models: Dict[LanguageModelClassification, LanguageModelConfiguration]
    execution_nature: ExecutionNature = ExecutionNature.SIMPLE
    prompt_strategy: strategies.NextAbilityConfiguration = None
    memory_provider_required: bool = False
    workspace_required: bool = False

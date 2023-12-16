from typing import Dict, List

from superpilot.core.configuration.schema import SystemConfiguration
from superpilot.core.planning.base import PromptStrategy
from superpilot.core.planning.settings import (
    LanguageModelConfiguration,
    PromptStrategyConfiguration,
    LanguageModelClassification
)
from superpilot.core.pilot.settings import (
    PilotConfiguration, ExecutionNature,
)


class TaskPilotConfiguration(SystemConfiguration):
    """Struct for model configuration."""

    from superpilot.core.plugin.base import PluginLocation
    location: PluginLocation
    models: Dict[LanguageModelClassification, LanguageModelConfiguration]
    pilot: PilotConfiguration = None
    execution_nature: ExecutionNature = ExecutionNature.SIMPLE
    callbacks: List[PluginLocation] = None
    prompt_strategy: SystemConfiguration = None
    memory_provider_required: bool = False
    workspace_required: bool = False

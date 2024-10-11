from pydantic import BaseModel
from superpilot.core.configuration import SystemConfiguration, SystemSettings
from superpilot.core.configuration.schema import WorkspaceSettings
from superpilot.core.memory.settings import MemorySettings
from superpilot.core.planning.settings import PlannerSettingsLegacy, PlannerSettings
from superpilot.core.plugin.base import PluginLocation
from superpilot.core.resource.model_providers.openai import OpenAISettings


class EnvSystems(SystemConfiguration):
    ability_registry: PluginLocation
    memory: PluginLocation
    openai_provider: PluginLocation
    planning: PluginLocation
    workspace: PluginLocation


class EnvConfiguration(SystemConfiguration):
    creation_time: str
    request_id: str
    systems: EnvSystems


class EnvSystemSettings(SystemSettings):
    configuration: EnvConfiguration


class EnvSettings(BaseModel):
    environment: EnvSystemSettings
    memory: MemorySettings
    openai_provider: OpenAISettings
    planning: PlannerSettings
    workspace: WorkspaceSettings

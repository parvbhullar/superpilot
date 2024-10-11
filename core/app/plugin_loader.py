from typing import Dict, Any, Optional, TYPE_CHECKING
from superpilot.core.plugin.simple import (
    PluginLocation,
    PluginStorageFormat,
    SimplePluginService,
)
if TYPE_CHECKING:
    from superpilot.core.plugin.base import PluginType


class PluginSchema:
    def __init__(self, name: str, goals: Optional[str] = None,
                 role: Optional[str] = None, plugin_storage: Optional[str] = None, **kwargs):
        self.name = name
        self.role = role
        self.goals = goals
        self.plugin_storage = plugin_storage
        self.kwargs = kwargs
        self.plugin = None


class PluginContainer:
    def __init__(self, plugin_configuration: Dict[str, Dict[str, str]]):
        self.plugins = {}
        for system_name, config in plugin_configuration.items():
            location = {
                "storage_format": PluginStorageFormat.INSTALLED_PACKAGE,
                "storage_route": config["plugin_path"]
            }
            plugin = PluginSchema(system_name, **config)
            plugin.plugin = SimplePluginService.get_plugin(location)
            self.plugins[system_name] = plugin

    def search_plugin(self, system_name: str):
        return self.plugins.get(system_name)

    @classmethod
    def factory(cls, config=None):
        if config is None:
            config = {
            "ability_registry": {
                "goals": "INSTALLED_PACKAGE",
                "role": "",
                "plugin_path": "superpilot.core.ability.SimpleAbilityRegistry",
            },
            "memory": {
                "plugin_path": "superpilot.core.memory.SimpleMemory",
            }
        }
        return cls(config)


if __name__ == "__main__":
    # Example usage
    plugin_configurations = {
        "ability_registry": {
            "goals": "INSTALLED_PACKAGE",
            "role": "",
            "plugin_path": "superpilot.core.ability.SimpleAbilityRegistry",
        },
        "memory": {
            "plugin_path": "superpilot.core.memory.SimpleMemory",
        }
    }

    container = PluginContainer(plugin_configurations)
    ability_registry = container.search_plugin("ability_registry")
    memory_plugin = container.search_plugin("memory")

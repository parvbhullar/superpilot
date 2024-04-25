from importlib import import_module
from typing import TYPE_CHECKING

from superpilot.core.plugin.base import (
    PluginLocation,
    PluginService,
    PluginStorageFormat,
    PluginStorageRoute,
)

if TYPE_CHECKING:
    from superpilot.core.plugin.base import PluginType


class ResearchPluginService(PluginService):
    @staticmethod
    def get_plugin(plugin_location) -> "PluginType":
        """Get a plugin from a plugin location."""
        if isinstance(plugin_location, dict):
            # plugin_location = PluginLocation.model_validate(plugin_location)
            plugin_location = PluginLocation.parse_obj(plugin_location)
        if plugin_location.storage_format == PluginStorageFormat.WORKSPACE:
            return ResearchPluginService.load_from_workspace(
                plugin_location.storage_route
            )
        elif plugin_location.storage_format == PluginStorageFormat.INSTALLED_PACKAGE:
            return ResearchPluginService.load_from_installed_package(
                plugin_location.storage_route
            )
        else:
            raise NotImplementedError(
                f"Plugin storage format {plugin_location.storage_format} is not implemented."
            )

    ####################################
    # Low-level storage format loaders #
    ####################################
    @staticmethod
    def load_from_file_path(plugin_route: PluginStorageRoute) -> "PluginType":
        """Load a plugin from a file path."""
        # TODO: Define an on disk storage format and implement this.
        #   Can pull from existing zip file loading implementation
        raise NotImplementedError("Loading from file path is not implemented.")

    @staticmethod
    def load_from_import_path(plugin_route: PluginStorageRoute) -> "PluginType":
        """Load a plugin from an import path."""
        module_path, _, class_name = plugin_route.rpartition(".")
        return getattr(import_module(module_path), class_name)

    @staticmethod
    def resolve_name_to_path(
        plugin_route: PluginStorageRoute, path_type: str
    ) -> PluginStorageRoute:
        """Resolve a plugin name to a plugin path."""
        # TODO: Implement a discovery system for finding plugins by name from known
        #   storage locations. E.g. if we know that path_type is a file path, we can
        #   search the workspace for it. If it's an import path, we can check the core
        #   system and the superpilot_plugins package.
        raise NotImplementedError("Resolving plugin name to path is not implemented.")

    #####################################
    # High-level storage format loaders #
    #####################################

    @staticmethod
    def load_from_workspace(plugin_route: PluginStorageRoute) -> "PluginType":
        """Load a plugin from the workspace."""
        plugin = ResearchPluginService.load_from_file_path(plugin_route)
        return plugin

    @staticmethod
    def load_from_installed_package(plugin_route: PluginStorageRoute) -> "PluginType":
        plugin = ResearchPluginService.load_from_import_path(plugin_route)
        return plugin

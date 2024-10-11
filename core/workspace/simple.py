import logging
import typing
from pathlib import Path

from superpilot.core.configuration import (
    Configurable,
    WorkspaceSettings,
    WorkspaceConfiguration,
    WorkspaceSetup,
)
from superpilot.core.workspace.base import Workspace


class SimpleWorkspace(Configurable, Workspace, WorkspaceSetup):
    default_settings = WorkspaceSettings(
        name="workspace",
        description="The workspace is the root directory for all pilot activity.",
        configuration=WorkspaceConfiguration(
            root="",
            parent="~/superpilot/environments",
            restrict_to_workspace=True,
        ),
    )

    NULL_BYTES = ["\0", "\000", "\x00", "\u0000", "%00"]

    def __init__(
        self,
        settings: WorkspaceSettings,
        logger: logging.Logger,
    ):
        self._configuration = settings.configuration
        self._logger = logger.getChild("workspace")

    @property
    def root(self) -> Path:
        return Path(self._configuration.root)

    @property
    def debug_log_path(self) -> Path:
        return self.root / "logs" / "debug.log"

    @property
    def cycle_log_path(self) -> Path:
        return self.root / "logs" / "cycle.log"

    @property
    def configuration_path(self) -> Path:
        return self.root / "configuration.yml"

    @property
    def restrict_to_workspace(self) -> bool:
        return self._configuration.restrict_to_workspace

    def get_path(self, relative_path: typing.Union[str, Path]) -> Path:
        """Get the full path for an item in the workspace.

        Parameters
        ----------
        relative_path
            The relative path to resolve in the workspace.

        Returns
        -------
        Path
            The resolved path relative to the workspace.

        """
        return self._sanitize_path(
            relative_path,
            root=self.root,
            restrict_to_root=self.restrict_to_workspace,
        )

    def _sanitize_path(
        self,
        relative_path: typing.Union[str, Path],
        root: typing.Union[str, Path] = None,
        restrict_to_root: bool = True,
    ) -> Path:
        """Resolve the relative path within the given root if possible.

        Parameters
        ----------
        relative_path
            The relative path to resolve.
        root
            The root path to resolve the relative path within.
        restrict_to_root
            Whether to restrict the path to the root.

        Returns
        -------
        Path
            The resolved path.

        Raises
        ------
        ValueError
            If the path is absolute and a root is provided.
        ValueError
            If the path is outside the root and the root is restricted.

        """

        # Posix systems disallow null bytes in paths. Windows is agnostic about it.
        # Do an explicit check here for all sorts of null byte representations.

        for null_byte in self.NULL_BYTES:
            if null_byte in str(relative_path) or null_byte in str(root):
                raise ValueError("embedded null byte")

        if root is None:
            return Path(relative_path).resolve()

        self._logger.debug(f"Resolving path '{relative_path}' in workspace '{root}'")
        root, relative_path = Path(root).resolve(), Path(relative_path)
        self._logger.debug(f"Resolved root as '{root}'")

        if relative_path.is_absolute():
            raise ValueError(
                f"Attempted to access absolute path '{relative_path}' in workspace '{root}'."
            )
        full_path = root.joinpath(relative_path).resolve()

        self._logger.debug(f"Joined paths as '{full_path}'")

        if restrict_to_root and not full_path.is_relative_to(root):
            raise ValueError(
                f"Attempted to access path '{full_path}' outside of workspace '{root}'."
            )

        return full_path

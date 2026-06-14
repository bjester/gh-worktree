import os
import shutil
from contextlib import contextmanager
from pathlib import Path

from treefort.config import (
    ConfigManager,
    ConfigProtocol,
    GlobalConfig,
    RepositoryConfig,
)
from treefort.errors import AncestorNotFoundError, ProjectNotFoundError
from treefort.utils import find_up


def migrate_old_config(old_dir: Path, new_dir: Path) -> bool:
    """
    Migrate configuration from old directory to new directory.

    :param old_dir: The old configuration directory path
    :param new_dir: The new configuration directory path
    :return: True if migration occurred, False otherwise
    """
    if not old_dir.exists():
        return False

    # Create new directory
    new_dir.mkdir(parents=True, exist_ok=True)

    # Copy all contents from old to new
    for item in old_dir.iterdir():
        src = item
        dst = new_dir / item.name
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    # Remove old directory if empty or after successful migration
    try:
        # Try to remove the old directory and its parents if they become empty
        shutil.rmtree(old_dir)
        # Clean up parent .gh directory if it's now empty
        parent_gh = old_dir.parent
        if parent_gh.exists() and parent_gh.is_dir() and not any(parent_gh.iterdir()):
            parent_gh.rmdir()
    except OSError:
        # Directory not empty or other error, leave it
        pass

    return True


class Context:
    def __init__(self):
        self.cwd = Path.cwd()
        self._cached_project_dir: Path | None = None
        self._migrated = False
        self._config_manager = ConfigManager()

    @property
    def project_dir(self) -> Path:
        if self._cached_project_dir is None:
            git_bare_dir = find_up(".bare", self.cwd)
            self._cached_project_dir = git_bare_dir.parent
        return self._cached_project_dir

    @property
    def config_dir(self) -> Path:
        return self.project_dir / ".treefort"

    @property
    def global_config_dir(self) -> Path:
        try:
            parent_dir = self.project_dir.parent
        except AncestorNotFoundError:
            parent_dir = self.cwd.parent

        try:
            return find_up(".treefort", parent_dir)
        except AncestorNotFoundError:
            # default to ~/.treefort
            return Path.home() / ".treefort"

    @contextmanager
    def use(self, cwd: str | Path):
        old_cwd = self.cwd
        cwd_path = Path(cwd)
        os.chdir(cwd_path)
        self.cwd = cwd_path
        try:
            yield
        finally:
            os.chdir(old_cwd)
            self.cwd = old_cwd

    def migrate(self):
        skip_project_config = False
        try:
            parent_dir = self.project_dir.parent
        except AncestorNotFoundError:
            parent_dir = self.cwd.parent
            skip_project_config = True

        # migrate global config
        try:
            closest_gh_dir = find_up(".gh", parent_dir)
            old_global_config_dir = closest_gh_dir / "worktree"
            new_global_config_dir = closest_gh_dir.parent / ".treefort"
            if old_global_config_dir.exists():
                migrate_old_config(old_global_config_dir, new_global_config_dir)
        except AncestorNotFoundError:
            pass

        if skip_project_config:
            return

        # migrate project config
        try:
            old_config_dir = self.project_dir / ".gh" / "worktree"
            new_config_dir = self.project_dir / ".treefort"
            if old_config_dir.exists():
                migrate_old_config(old_config_dir, new_config_dir)
        except AncestorNotFoundError:
            pass

    def reset_properties(self):
        """Resets any cached properties"""
        self._cached_project_dir = None

    def assert_within_project(self):
        try:
            find_up(".bare", self.cwd)
        except AncestorNotFoundError as e:
            raise ProjectNotFoundError("Project not found") from e

    def get_config(self) -> RepositoryConfig:
        """Get the repository configuration."""
        return self._config_manager.get_config(self.config_dir)

    def get_global_config(self) -> GlobalConfig:
        """Get the global configuration."""
        return self._config_manager.get_global_config(self.global_config_dir)

    def set_config(self, config: ConfigProtocol):
        """Save a configuration to disk."""
        self._config_manager.save_config(config)

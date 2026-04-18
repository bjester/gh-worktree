import os
from contextlib import contextmanager
from pathlib import Path

from gh_worktree.config import Config, GlobalConfig, RepositoryConfig
from gh_worktree.errors import AncestorNotFoundError, ConfigTypeError, ProjectNotFoundError
from gh_worktree.utils import find_up


class Context:
    def __init__(self):
        self.cwd = Path.cwd()
        self._cached_project_dir: Path | None = None

    @property
    def project_dir(self) -> Path:
        if self._cached_project_dir is None:
            git_bare_dir = find_up(".bare", self.cwd)
            self._cached_project_dir = git_bare_dir.parent
        return self._cached_project_dir

    @property
    def config_dir(self) -> Path:
        return self.project_dir / ".gh" / "worktree"

    @property
    def global_config_dir(self) -> Path:
        try:
            parent_dir = self.project_dir.parent
        except AncestorNotFoundError:
            parent_dir = self.cwd.parent

        try:
            closest_gh_dir = find_up(".gh", parent_dir)
            return closest_gh_dir / "worktree"
        except AncestorNotFoundError:
            # default to ~/.gh/worktree
            return Path.home() / ".gh" / "worktree"

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

    def reset_properties(self):
        """Resets any cached properties"""
        self._cached_project_dir = None

    def assert_within_project(self):
        try:
            find_up(".bare", self.cwd)
        except AncestorNotFoundError as e:
            raise ProjectNotFoundError("Project not found") from e

    def get_config(self) -> RepositoryConfig:
        file_path = self.config_dir / "config.json"
        if not file_path.exists():
            return RepositoryConfig()

        with file_path.open("r", encoding="utf-8") as f:
            return RepositoryConfig.load(f)

    def get_global_config(self):
        file_path = self.global_config_dir / "config.json"
        if not file_path.exists():
            return GlobalConfig()

        with file_path.open("r", encoding="utf-8") as f:
            return GlobalConfig.load(f)

    def set_config(self, config: Config):
        if isinstance(config, RepositoryConfig):
            config_dir = self.config_dir
        elif isinstance(config, GlobalConfig):
            config_dir = self.global_config_dir
        else:
            raise ConfigTypeError(f"Unknown config type: {type(config)}")

        config_dir.mkdir(parents=True, exist_ok=True)
        with (config_dir / "config.json").open("w", encoding="utf-8") as f:
            config.save(f)

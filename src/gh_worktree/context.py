import os
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from typing import Union

from gh_worktree.config import Config
from gh_worktree.config import GlobalConfig
from gh_worktree.config import RepositoryConfig
from gh_worktree.utils import find_up


class Context(object):
    def __init__(self):
        self.cwd = Path.cwd()

    @cached_property
    def project_dir(self) -> Path:
        git_bare_dir = find_up(".bare", self.cwd)
        return git_bare_dir.parent

    @property
    def config_dir(self) -> Path:
        return self.project_dir / ".gh" / "worktree"

    @property
    def global_config_dir(self) -> Path:
        try:
            parent_dir = self.project_dir.parent
        except RuntimeError:
            parent_dir = self.cwd.parent

        try:
            closest_gh_dir = find_up(".gh", parent_dir)
            return closest_gh_dir / "worktree"
        except RuntimeError:
            # default to ~/.gh/worktree
            return Path.home() / ".gh" / "worktree"

    @contextmanager
    def use(self, cwd: Union[str, Path]):
        old_cwd = self.cwd
        cwd_path = Path(cwd)
        os.chdir(cwd_path)
        self.cwd = cwd_path
        try:
            yield
        finally:
            os.chdir(old_cwd)
            self.cwd = old_cwd

    def assert_within_project(self):
        try:
            find_up(".bare", self.cwd)
        except RuntimeError:
            raise AssertionError("Project not found")

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
            raise ValueError(f"Unknown config type: {type(config)}")

        config_dir.mkdir(parents=True, exist_ok=True)
        with (config_dir / "config.json").open("w", encoding="utf-8") as f:
            config.save(f)

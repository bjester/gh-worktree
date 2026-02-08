import os
from contextlib import contextmanager
from functools import cached_property

from gh_worktree.config import Config
from gh_worktree.config import RepositoryConfig
from gh_worktree.config import GlobalConfig
from gh_worktree.utils import find_up


class Context(object):
    def __init__(self):
        self.cwd = os.getcwd()

    @cached_property
    def project_dir(self) -> str:
        git_bare_dir = find_up(".bare", self.cwd)
        return os.path.dirname(git_bare_dir)

    @property
    def config_dir(self) -> str:
        return os.path.join(self.project_dir, ".gh", "worktree")

    @property
    def global_config_dir(self) -> str:
        try:
            parent_dir = os.path.dirname(self.project_dir)
        except RuntimeError:
            parent_dir = os.path.dirname(self.cwd)

        try:
            closest_gh_dir = find_up(".gh", parent_dir)
            return os.path.join(closest_gh_dir, "worktree")
        except RuntimeError:
            # default to ~/.gh/worktree
            return os.path.join(os.path.expanduser("~"), ".gh", "worktree")

    @contextmanager
    def use(self, cwd: str):
        old_cwd = self.cwd
        os.chdir(cwd)
        self.cwd = cwd
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
        file_path = os.path.join(self.config_dir, "config.json")
        if not os.path.exists(file_path):
            return RepositoryConfig()

        with open(file_path, "r") as f:
            return RepositoryConfig.load(f)

    def get_global_config(self):
        file_path = os.path.join(self.global_config_dir, "config.json")
        if not os.path.exists(file_path):
            return GlobalConfig()

        with open(file_path, "r") as f:
            return GlobalConfig.load(f)

    def set_config(self, config: Config):
        if isinstance(config, RepositoryConfig):
            config_dir = self.config_dir
        elif isinstance(config, GlobalConfig):
            config_dir = self.global_config_dir
        else:
            raise ValueError(f"Unknown config type: {type(config)}")

        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "config.json"), "w") as f:
            config.save(f)

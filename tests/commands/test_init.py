from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gh_worktree.commands.init import InitCommand, RepositoryTarget, normalize
from gh_worktree.hooks import Hook


class StubContext:
    def __init__(self, cwd, config_dir):
        self.cwd = str(cwd)
        self.config_dir = str(config_dir)

    @contextmanager
    def use(self, cwd):
        old_cwd = self.cwd
        self.cwd = str(cwd)
        try:
            yield
        finally:
            self.cwd = old_cwd


def test_normalize_owner_repo():
    assert normalize("octo/repo") == "https://github.com/octo/repo.git"


def test_normalize_invalid_repo():
    with pytest.raises(ValueError, match="Invalid repository path format"):
        normalize("not a repo")


def test_repository_target_parses_ssh_uri():
    target = RepositoryTarget("git@github.com:octo/repo.git")
    assert target.path == "octo/repo.git"
    assert target.owner == "octo"
    assert target.name == "repo"


def test_init_command_writes_gitdir_and_config(tmp_path):
    project_dir = tmp_path / "project"
    config_dir = tmp_path / "config"
    context = StubContext(tmp_path, config_dir)

    hooks = SimpleNamespace(fire=Mock())
    git = SimpleNamespace(clone=Mock(), config=Mock(), fetch=Mock())
    gh = SimpleNamespace(
        repo_status=Mock(
            return_value={
                "defaultBranchRef": {"name": "main"},
                "owner": {"login": "octo"},
                "name": "repo",
                "url": "https://github.com/octo/repo",
                "isPrivate": False,
            }
        )
    )
    runtime = SimpleNamespace(context=context, hooks=hooks, git=git, gh=gh)

    command = InitCommand(runtime)
    command("octo/repo", str(project_dir))

    git.clone.assert_called_once_with("https://github.com/octo/repo.git", ".bare")
    git.config.assert_called_once_with(
        "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"
    )
    git.fetch.assert_called_once_with()

    gitdir_file = project_dir / ".git"
    assert gitdir_file.read_text() == "gitdir: ./.bare"
    config_file = config_dir / "config.json"
    assert config_file.exists()

    hooks.fire.assert_any_call(
        Hook.pre_init,
        "https://github.com/octo/repo.git",
        str(project_dir),
        skip_project=True,
    )
    hooks.fire.assert_any_call(
        Hook.post_init,
        "https://github.com/octo/repo.git",
        str(project_dir),
        skip_project=True,
    )

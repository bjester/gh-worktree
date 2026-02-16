from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

from gh_worktree.commands.create import CreateCommand
from gh_worktree.git import GitRemote
from gh_worktree.hooks import Hook


class StubContext:
    def __init__(self, project_dir, config):
        self.project_dir = str(project_dir)
        self._config = config
        self.assert_called = False

    def assert_within_project(self):
        self.assert_called = True

    def get_config(self):
        return self._config

    @contextmanager
    def use(self, cwd):
        yield


def test_create_command_uses_default_branch_and_remote():
    context = StubContext("/repo", SimpleNamespace(default_branch="main"))
    hooks = SimpleNamespace(fire=Mock())
    git = SimpleNamespace(fetch=Mock(), add_worktree=Mock())
    templates = SimpleNamespace(copy=Mock())
    runtime = SimpleNamespace(
        context=context,
        hooks=hooks,
        git=git,
        templates=templates,
        get_remote=Mock(return_value=GitRemote("origin", "uri", "fetch")),
    )

    command = CreateCommand(runtime)
    command("feature")

    assert context.assert_called is True
    runtime.get_remote.assert_called_once_with()
    git.fetch.assert_called_once_with("origin")
    git.add_worktree.assert_called_once_with("feature", "origin/main")
    templates.copy.assert_called_once_with("feature")
    hooks.fire.assert_any_call(Hook.pre_create, "feature", "origin/main")
    hooks.fire.assert_any_call(Hook.post_create, "feature", "origin/main")


def test_create_command_respects_explicit_remote_and_ref():
    context = StubContext("/repo", SimpleNamespace(default_branch="main"))
    hooks = SimpleNamespace(fire=Mock())
    git = SimpleNamespace(fetch=Mock(), add_worktree=Mock())
    templates = SimpleNamespace(copy=Mock())
    runtime = SimpleNamespace(
        context=context,
        hooks=hooks,
        git=git,
        templates=templates,
        get_remote=Mock(),
    )

    command = CreateCommand(runtime)
    command("feature", "upstream/dev")

    runtime.get_remote.assert_not_called()
    git.fetch.assert_called_once_with("upstream")
    git.add_worktree.assert_called_once_with("feature", "upstream/dev")
    templates.copy.assert_called_once_with("feature")
    hooks.fire.assert_any_call(Hook.pre_create, "feature", "upstream/dev")
    hooks.fire.assert_any_call(Hook.post_create, "feature", "upstream/dev")

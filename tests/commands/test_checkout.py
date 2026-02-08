from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock, ANY

import pytest

from gh_worktree.commands.checkout import CheckoutCommand
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


def test_checkout_command_uses_branch_name():
    config = SimpleNamespace(url="https://github.com/octo/repo")
    context = StubContext("/repo", config)
    hooks = SimpleNamespace(fire=Mock())
    git = SimpleNamespace(open_worktree=Mock())
    runtime = SimpleNamespace(
        context=context,
        hooks=hooks,
        git=git,
        get_remote=Mock(return_value=GitRemote("origin", "uri", "fetch")),
    )

    command = CheckoutCommand(runtime)
    command("feature")

    assert context.assert_called is True
    runtime.get_remote.assert_called_once_with()
    git.open_worktree.assert_called_once_with("feature")
    hooks.fire.assert_any_call(Hook.pre_checkout, "feature", ANY)
    hooks.fire.assert_any_call(Hook.post_checkout, "feature", ANY)


def test_checkout_command_raises_on_missing_remote():
    config = SimpleNamespace(url="https://github.com/octo/repo")
    context = StubContext("/repo", config)
    runtime = SimpleNamespace(
        context=context,
        hooks=SimpleNamespace(fire=Mock()),
        git=SimpleNamespace(open_worktree=Mock()),
        get_remote=Mock(return_value=None),
    )

    command = CheckoutCommand(runtime)

    with pytest.raises(ValueError, match="Couldn't determine default remote"):
        command("feature")


def test_checkout_command_rejects_invalid_pull_url():
    config = SimpleNamespace(url="https://github.com/octo/repo")
    context = StubContext("/repo", config)
    runtime = SimpleNamespace(
        context=context,
        hooks=SimpleNamespace(fire=Mock()),
        git=SimpleNamespace(open_worktree=Mock()),
        get_remote=Mock(return_value=GitRemote("origin", "uri", "fetch")),
    )

    command = CheckoutCommand(runtime)

    with pytest.raises(AssertionError, match="Invalid pull request URL"):
        command("https://github.com/octo/repo/issues/12")

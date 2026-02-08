from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gh_worktree.commands.remove import RemoveCommand
from gh_worktree.hooks import Hook


class StubContext:
    def __init__(self, project_dir):
        self.project_dir = str(project_dir)

    @contextmanager
    def use(self, cwd):
        yield


def test_remove_command_raises_when_missing(tmp_path):
    context = StubContext(tmp_path)
    runtime = SimpleNamespace(
        context=context,
        hooks=SimpleNamespace(fire=Mock()),
        git=SimpleNamespace(remove_worktree=Mock()),
    )

    command = RemoveCommand(runtime)

    with pytest.raises(ValueError, match="Worktree missing does not exist"):
        command("missing")


def test_remove_command_runs_hooks_and_git(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "feature").mkdir()

    context = StubContext(project_dir)
    hooks = SimpleNamespace(fire=Mock())
    git = SimpleNamespace(remove_worktree=Mock())
    runtime = SimpleNamespace(context=context, hooks=hooks, git=git)

    command = RemoveCommand(runtime)
    command("feature", force=True)

    git.remove_worktree.assert_called_once_with("feature", force=True)
    hooks.fire.assert_any_call(Hook.pre_remove, "feature")
    hooks.fire.assert_any_call(Hook.post_remove, "feature")

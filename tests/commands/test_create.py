from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from gh_worktree.commands.create import CreateCommand
from gh_worktree.git import GitRemote
from gh_worktree.hooks import Hook


class StubContext:
    def __init__(self, project_dir, config):
        self.project_dir = project_dir
        self._config = config
        self.assert_called = False

    def assert_within_project(self):
        self.assert_called = True

    def get_config(self):
        return self._config

    @contextmanager
    def use(self, cwd):
        yield


class CreateCommandTestCase(TestCase):
    def setUp(self):
        self.config = SimpleNamespace(default_branch="main")
        self.context = StubContext(Path("/repo"), self.config)
        self.hooks = SimpleNamespace(fire=Mock())
        self.git = SimpleNamespace(fetch=Mock(), add_worktree=Mock())
        self.templates = SimpleNamespace(copy=Mock())
        self.runtime = SimpleNamespace(
            context=self.context,
            hooks=self.hooks,
            git=self.git,
            templates=self.templates,
            get_remote=Mock(return_value=GitRemote("origin", "uri", "fetch")),
        )
        self.command = CreateCommand(self.runtime)

    def test_call__uses_default_branch_and_remote(self):
        self.command("feature")

        self.assertTrue(self.context.assert_called)
        self.runtime.get_remote.assert_called_once_with()
        self.git.fetch.assert_called_once_with("origin")
        self.git.add_worktree.assert_called_once_with("feature", "origin/main")
        self.templates.copy.assert_called_once_with("feature")
        self.hooks.fire.assert_any_call(Hook.pre_create, "feature", "origin/main")
        self.hooks.fire.assert_any_call(Hook.post_create, "feature", "origin/main")

    def test_call__respects_explicit_remote_and_ref(self):
        self.command("feature", "upstream/dev")

        self.assertTrue(self.context.assert_called)
        self.runtime.get_remote.assert_not_called()
        self.git.fetch.assert_called_once_with("upstream")
        self.git.add_worktree.assert_called_once_with("feature", "upstream/dev")
        self.templates.copy.assert_called_once_with("feature")
        self.hooks.fire.assert_any_call(Hook.pre_create, "feature", "upstream/dev")
        self.hooks.fire.assert_any_call(Hook.post_create, "feature", "upstream/dev")

    def test_call__handles_ref_with_slashes(self):
        self.command("feature", "upstream/some/nested/branch")

        self.assertTrue(self.context.assert_called)
        self.runtime.get_remote.assert_not_called()
        self.git.fetch.assert_called_once_with("upstream")
        self.git.add_worktree.assert_called_once_with(
            "feature", "upstream/some/nested/branch"
        )
        self.templates.copy.assert_called_once_with("feature")
        self.hooks.fire.assert_any_call(
            Hook.pre_create, "feature", "upstream/some/nested/branch"
        )
        self.hooks.fire.assert_any_call(
            Hook.post_create, "feature", "upstream/some/nested/branch"
        )

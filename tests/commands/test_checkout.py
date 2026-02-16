from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import ANY
from unittest.mock import Mock

from gh_worktree.commands.checkout import CheckoutCommand
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


class CheckoutCommandTestCase(TestCase):
    def setUp(self):
        self.config = SimpleNamespace(
            url="https://github.com/octo/repo",
            owner="octo",
            name="repo",
        )
        self.context = StubContext(Path("/repo"), self.config)
        self.hooks = SimpleNamespace(fire=Mock())
        self.git = SimpleNamespace(open_worktree=Mock(), fetch=Mock())
        self.gh = SimpleNamespace(pr_status=Mock())
        self.templates = SimpleNamespace(copy=Mock())
        self.runtime = SimpleNamespace(
            context=self.context,
            hooks=self.hooks,
            git=self.git,
            gh=self.gh,
            templates=self.templates,
            get_remote=Mock(return_value=GitRemote("origin", "uri", "fetch")),
            get_default_remote=Mock(return_value=GitRemote("origin", "uri", "fetch")),
        )
        self.command = CheckoutCommand(self.runtime)

    def test_call__uses_branch_name(self):
        self.command("feature")

        self.assertTrue(self.context.assert_called)

        self.git.fetch.assert_called_once_with("origin", "feature:feature")
        self.runtime.get_remote.assert_called_once_with(owner_name="octo")
        self.git.open_worktree.assert_called_once_with("feature")
        self.templates.copy.assert_called_once_with("feature")
        self.hooks.fire.assert_any_call(Hook.pre_checkout, "feature", ANY)
        self.hooks.fire.assert_any_call(Hook.post_checkout, "feature", ANY)

    def test_call__uses_remote_and_branch_name(self):
        self.command("feature", remote="aremote")

        self.assertTrue(self.context.assert_called)

        self.git.fetch.assert_called_once_with("aremote", "feature:feature")
        self.git.open_worktree.assert_called_once_with("feature")
        self.templates.copy.assert_called_once_with("feature")
        self.hooks.fire.assert_any_call(Hook.pre_checkout, "feature", ANY)
        self.hooks.fire.assert_any_call(Hook.post_checkout, "feature", ANY)

    def test_call__uses_pr_number(self):
        self.gh.pr_status.return_value = {
            "headRefName": "feature",
        }

        self.command("1234")

        self.assertTrue(self.context.assert_called)
        self.gh.pr_status.assert_called_once_with("1234", owner_repo="octo/repo")
        self.runtime.get_remote.assert_called_once_with(owner_name="octo")
        self.git.open_worktree.assert_called_once_with("feature")
        self.templates.copy.assert_called_once_with("feature")
        self.hooks.fire.assert_any_call(Hook.pre_checkout, "feature", ANY)
        self.hooks.fire.assert_any_call(Hook.post_checkout, "feature", ANY)

    def test_call__uses_pr_url(self):
        self.gh.pr_status.return_value = {
            "headRefName": "feature",
        }

        self.command("https://github.com/octo/repo/pull/1234")

        self.assertTrue(self.context.assert_called)
        self.gh.pr_status.assert_called_once_with("1234", owner_repo="octo/repo")
        self.runtime.get_remote.assert_called_once_with(owner_name="octo")
        self.git.open_worktree.assert_called_once_with("feature")
        self.templates.copy.assert_called_once_with("feature")
        self.hooks.fire.assert_any_call(Hook.pre_checkout, "feature", ANY)
        self.hooks.fire.assert_any_call(Hook.post_checkout, "feature", ANY)

    def test_call__raises_on_missing_remote(self):
        self.runtime.get_remote.return_value = None

        with self.assertRaises(AssertionError, msg="Couldn't find matching remote"):
            self.command("feature")

    def test_call__rejects_invalid_pull_url(self):
        with self.assertRaises(ValueError, msg="Couldn't parse input. Must be"):
            self.command("https://github.com/octo/repo/issues/12")

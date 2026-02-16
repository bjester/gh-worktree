import pathlib
import tempfile
from contextlib import contextmanager
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import Mock

from gh_worktree.commands.init import InitCommand
from gh_worktree.commands.init import normalize
from gh_worktree.commands.init import RepositoryTarget
from gh_worktree.hooks import Hook


class StubContext:
    def __init__(self, cwd, config_dir):
        self.cwd = cwd
        self.config_dir = config_dir

    @contextmanager
    def use(self, cwd):
        old_cwd = self.cwd
        self.cwd = cwd
        try:
            yield
        finally:
            self.cwd = old_cwd


class NormalizeTestCase(TestCase):
    def test_owner_repo(self):
        self.assertEqual(normalize("octo/repo"), "https://github.com/octo/repo.git")

    def test_no_dot_git(self):
        self.assertEqual(
            normalize("https://github.com/octo/repo"),
            "https://github.com/octo/repo.git",
        )

    def test_ssh(self):
        self.assertEqual(
            normalize("git@github.com:octo/repo.git"),
            "git@github.com:octo/repo.git",
        )

    def test_invalid_repo(self):
        with self.assertRaisesRegex(ValueError, "Invalid repository path format"):
            normalize("not a repo")


class RepositoryTargetTestCase(TestCase):
    def test_validate(self):
        target = RepositoryTarget("https://github.com/octo/repo.git")
        target.validate()

    def test_validate__invalid_path(self):
        target = RepositoryTarget("https://github.com/octo/repo/pull/123.git")
        with self.assertRaises(
            ValueError, msg="Invalid repository path: octo/repo/pull/123"
        ):
            target.validate()

    def test_path__url(self):
        target = RepositoryTarget("https://github.com/octo/repo.git")
        self.assertEqual(target.path, "octo/repo.git")

    def test_path__ssh(self):
        target = RepositoryTarget("git@github.com:octo/repo.git")
        self.assertEqual(target.path, "octo/repo.git")

    def test_path__owner_repo(self):
        target = RepositoryTarget("octo/repo")
        self.assertEqual(target.path, "octo/repo.git")

    def test_owner(self):
        target = RepositoryTarget("https://github.com/octo/repo.git")
        self.assertEqual(target.owner, "octo")

    def test_repo(self):
        target = RepositoryTarget("https://github.com/octo/repo.git")
        self.assertEqual(target.name, "repo")

    def test_destination_dir__default(self):
        target = RepositoryTarget("octo/repo")
        self.assertEqual(target.destination_dir, "repo")

    def test_destination_dir__custom(self):
        target = RepositoryTarget("octo/repo", destination_dir="custom-dir")
        self.assertEqual(target.destination_dir, "custom-dir")


class InitCommandTestCase(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = pathlib.Path(self.tmp_dir.name)
        self.project_dir = pathlib.Path("project")
        self.config_dir = self.tmp_path / ".gh" / "worktree"
        self.context = StubContext(self.tmp_path, self.config_dir)

        self.hooks = SimpleNamespace(fire=Mock(), add=MagicMock())
        self.git = SimpleNamespace(
            clone=Mock(),
            config=Mock(),
            fetch=Mock(),
            ls_tree=Mock(return_value=iter([])),
            cat_file=Mock(return_value=iter([])),
        )
        self.gh = SimpleNamespace(
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
        self.runtime = SimpleNamespace(
            context=self.context, hooks=self.hooks, git=self.git, gh=self.gh
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_call__basic(self):
        command = InitCommand(self.runtime)
        command("octo/repo", str(self.project_dir))

        self.git.clone.assert_called_once_with(
            "https://github.com/octo/repo.git", ".bare"
        )
        self.git.config.assert_called_once_with(
            "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"
        )
        self.git.fetch.assert_called_once_with()

        gitdir_file = self.tmp_path / self.project_dir / ".git"
        self.assertEqual(gitdir_file.read_text(), "gitdir: ./.bare")
        config_file = self.config_dir / "config.json"
        self.assertTrue(config_file.exists())

        self.hooks.fire.assert_any_call(
            Hook.pre_init,
            "https://github.com/octo/repo.git",
            self.tmp_path / self.project_dir,
            skip_project=True,
        )
        self.hooks.fire.assert_any_call(
            Hook.post_init,
            "https://github.com/octo/repo.git",
            self.tmp_path / self.project_dir,
        )

    def test_call__installs_hooks(self):

        def ls_tree_side_effect(branch, path):
            if path.endswith("post_checkout"):
                return iter(["100755 blob ...    post_checkout"])
            return iter([])

        self.git.ls_tree.side_effect = ls_tree_side_effect
        self.git.cat_file.return_value = iter(["echo 'hello'"])

        mock_f = self.runtime.hooks.add.return_value.__enter__.return_value

        command = InitCommand(self.runtime)
        command("octo/repo", str(self.project_dir))

        mock_f.write.assert_called_once_with("echo 'hello'\n")

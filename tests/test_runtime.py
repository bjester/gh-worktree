from types import SimpleNamespace
from unittest import TestCase

from gh_worktree.git import GitRemote
from gh_worktree.runtime import Runtime


class RuntimeTestCase(TestCase):
    def setUp(self):
        self.runtime = Runtime()
        self.config = SimpleNamespace(owner="octo", name="repo")
        self.runtime.context = SimpleNamespace(
            get_config=lambda: self.config,
        )
        self.remotes = [
            GitRemote("origin", "git@github.com:octo/repo.git", "fetch"),
            GitRemote("origin", "git@github.com:octo/repo.git", "push"),
            GitRemote("other", "git@github.com:other/repo.git", "fetch"),
        ]
        self.runtime.git = SimpleNamespace(remote=lambda: self.remotes)

    def test_get_remote__no_args_raises(self):
        with self.assertRaises(
            ValueError, msg="Must provide either owner_name or name"
        ):
            self.runtime.get_remote()

    def test_get_remote__owner_name(self):
        remote = self.runtime.get_remote(owner_name="octo")
        self.assertEqual(remote, self.remotes[0])

    def test_get_remote__name(self):
        remote = self.runtime.get_remote(name="other")
        self.assertEqual(remote, self.remotes[2])

    def test_get_remote__not_found(self):
        remote = self.runtime.get_remote(name="test")
        self.assertIsNone(remote)

    def test_get_default_remote(self):
        remote = self.runtime.get_default_remote()
        self.assertEqual(remote, self.remotes[0])

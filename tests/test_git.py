from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from unittest import TestCase

from gh_worktree.git import GitCLI
from gh_worktree.git import GitRemote


class GitCLITestCase(TestCase):
    def setUp(self):
        self.context = SimpleNamespace(cwd=Path("/test/tmp"))
        self.cli = GitCLI(self.context)

        stream_exec_patcher = mock.patch("gh_worktree.git.stream_exec")
        self.mock_stream_exec = stream_exec_patcher.start()
        self.addCleanup(stream_exec_patcher.stop)
        self.mock_stream_exec.return_value = 0

        iter_output_patcher = mock.patch("gh_worktree.git.iter_output")
        self.mock_iter_output = iter_output_patcher.start()
        self.addCleanup(iter_output_patcher.stop)

    def test_stream_exec(self):
        self.cli._stream_exec("foo", "bar")
        self.mock_stream_exec.assert_called_once_with(
            ["git", "foo", "bar"], cwd=Path("/test/tmp")
        )

    def test_stream_exec__fail(self):
        self.mock_stream_exec.return_value = 1
        with self.assertRaises(RuntimeError):
            self.cli._stream_exec("foo", "bar")
        self.mock_stream_exec.assert_called_once_with(
            ["git", "foo", "bar"], cwd=Path("/test/tmp")
        )

    def test_iter_output(self):
        self.mock_iter_output.return_value = ["line1", "line2"]
        lines = list(self.cli._iter_output("foo", "bar"))
        self.mock_iter_output.assert_called_once_with(
            ["git", "foo", "bar"], cwd=Path("/test/tmp")
        )
        self.assertEqual(lines, ["line1", "line2"])

    def test_clone(self):
        self.cli.clone("src_uri", "dest_dir")
        self.mock_stream_exec.assert_called_once_with(
            ["git", "clone", "--bare", "src_uri", "dest_dir"], cwd=Path("/test/tmp")
        )

    def test_config(self):
        self.cli.config("user.name", "foo")
        self.mock_stream_exec.assert_called_once_with(
            ["git", "config", "user.name", "foo"], cwd=Path("/test/tmp")
        )

    def test_ls_tree(self):
        self.mock_iter_output.return_value = ["line1", "line2"]
        lines = list(self.cli.ls_tree("main", "path/to/file"))
        self.mock_iter_output.assert_called_once_with(
            ["git", "ls-tree", "-r", "main", "--", "path/to/file"],
            cwd=Path("/test/tmp"),
        )
        self.assertEqual(lines, ["line1", "line2"])

    def test_cat_file(self):
        self.mock_iter_output.return_value = ["content"]
        lines = list(self.cli.cat_file("main", "file.txt"))
        self.mock_iter_output.assert_called_once_with(
            ["git", "cat-file", "-p", "main:file.txt"], cwd=Path("/test/tmp")
        )
        self.assertEqual(lines, ["content"])

    def test_fetch(self):
        self.cli.fetch()
        self.mock_stream_exec.assert_called_with(
            ["git", "fetch", "origin"], cwd=Path("/test/tmp")
        )

        self.cli.fetch(remote="upstream", refspec="master")
        self.mock_stream_exec.assert_called_with(
            ["git", "fetch", "upstream", "master"], cwd=Path("/test/tmp")
        )

    def test_remote(self):
        self.mock_iter_output.return_value = [
            "origin\thttps://github.com/foo/bar (fetch)",
            "origin\thttps://github.com/foo/bar (push)",
        ]
        remotes = self.cli.remote()
        self.mock_iter_output.assert_called_once_with(
            ["git", "remote", "-v"], cwd=Path("/test/tmp")
        )
        self.assertEqual(
            remotes,
            [
                GitRemote("origin", "https://github.com/foo/bar", "fetch"),
                GitRemote("origin", "https://github.com/foo/bar", "push"),
            ],
        )

    def test_add_worktree(self):
        self.cli.add_worktree("new-branch", "main")
        self.mock_stream_exec.assert_called_once_with(
            ["git", "worktree", "add", "-b", "new-branch", "--", "new-branch", "main"],
            cwd=Path("/test/tmp"),
        )

    def test_open_worktree(self):
        self.cli.open_worktree("existing-branch")
        self.mock_stream_exec.assert_called_once_with(
            ["git", "worktree", "add", "--", "existing-branch"], cwd=Path("/test/tmp")
        )

    def test_open_worktree_validation(self):
        with self.assertRaises(ValueError):
            self.cli.open_worktree("../outside")
        with self.assertRaises(ValueError):
            self.cli.open_worktree("/absolute")

    def test_remove_worktree(self):
        self.cli.remove_worktree("old-tree")
        self.mock_stream_exec.assert_called_with(
            ["git", "worktree", "remove", "--", "old-tree"], cwd=Path("/test/tmp")
        )

        self.cli.remove_worktree("old-tree", force=True)
        self.mock_stream_exec.assert_called_with(
            ["git", "worktree", "remove", "--force", "--", "old-tree"],
            cwd=Path("/test/tmp"),
        )

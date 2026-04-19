from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock

from gh_worktree.errors import CommandError, WorktreeNameError
from gh_worktree.git import GitCLI, GitRemote
from gh_worktree.logger import setup_logger


class GitCLITestCase(TestCase):
    def setUp(self):
        self.context = SimpleNamespace(cwd=Path("/test/tmp"))
        self.logger = setup_logger("test")
        self.cli = GitCLI(self.context, self.logger)

        stream_exec_patcher = mock.patch("gh_worktree.git.SubprocessOperator.stream_exec")
        self.mock_stream_exec = stream_exec_patcher.start()
        self.addCleanup(stream_exec_patcher.stop)
        self.mock_stream_exec.return_value = 0

        iter_output_patcher = mock.patch("gh_worktree.git.SubprocessOperator.iter_output")
        self.mock_iter_output = iter_output_patcher.start()
        self.addCleanup(iter_output_patcher.stop)

    def test_stream_exec(self):
        self.cli.stream_exec(["foo", "bar"])
        self.mock_stream_exec.assert_called_once_with(["foo", "bar"], cwd=None)

    def test_stream_exec__cwd_passthrough(self):
        self.cli.stream_exec(["foo", "bar"], cwd="/tmp")
        self.mock_stream_exec.assert_called_once_with(["foo", "bar"], cwd="/tmp")

    def test_stream_exec__non_zero_exit(self):
        self.mock_stream_exec.return_value = 1
        with self.assertRaises(CommandError):
            self.cli.stream_exec(["foo", "bar"], cwd=None)

    def test_clone(self):
        self.cli.clone("src_uri", "dest_dir")
        self.mock_stream_exec.assert_called_once_with(
            ["clone", "--bare", "src_uri", "dest_dir"], cwd=None
        )

    def test_config(self):
        self.cli.config("user.name", "foo")
        self.mock_stream_exec.assert_called_once_with(["config", "user.name", "foo"], cwd=None)

    def test_ls_tree(self):
        self.mock_iter_output.return_value = ["line1", "line2"]
        lines = list(self.cli.ls_tree("main", "path/to/file"))
        self.mock_iter_output.assert_called_once_with(
            ["ls-tree", "-r", "main", "--", "path/to/file"],
        )
        self.assertEqual(lines, ["line1", "line2"])

    def test_cat_file(self):
        self.mock_iter_output.return_value = ["content"]
        lines = list(self.cli.cat_file("main", "file.txt"))
        self.mock_iter_output.assert_called_once_with(["cat-file", "-p", "main:file.txt"])
        self.assertEqual(lines, ["content"])

    def test_fetch(self):
        self.cli.fetch()
        self.mock_stream_exec.assert_called_with(["fetch", "origin"], cwd=None)

        self.cli.fetch(remote="upstream", refspec="master")
        self.mock_stream_exec.assert_called_with(["fetch", "upstream", "master"], cwd=None)

    def test_remote(self):
        self.mock_iter_output.return_value = [
            "origin\thttps://github.com/foo/bar (fetch)",
            "origin\thttps://github.com/foo/bar (push)",
        ]
        remotes = self.cli.remote()
        self.mock_iter_output.assert_called_once_with(["remote", "-v"])
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
            ["worktree", "add", "-b", "new-branch", "--", "new-branch", "main"], cwd=None
        )

    def test_open_worktree(self):
        self.cli.open_worktree("existing-branch")
        self.mock_stream_exec.assert_called_once_with(
            ["worktree", "add", "--", "existing-branch", "existing-branch"], cwd=None
        )

    def test_open_worktree__with_slash_in_name(self):
        self.cli.open_worktree("feature/existing-branch")
        self.mock_stream_exec.assert_called_once_with(
            [
                "worktree",
                "add",
                "--",
                "feature/existing-branch",
                "feature/existing-branch",
            ],
            cwd=None,
        )

    def test_open_worktree_validation(self):
        with self.assertRaises(WorktreeNameError):
            self.cli.open_worktree("../outside")
        with self.assertRaises(WorktreeNameError):
            self.cli.open_worktree("/absolute")

    def test_remove_worktree(self):
        self.cli.remove_worktree("old-tree")
        self.mock_stream_exec.assert_called_with(["worktree", "remove", "--", "old-tree"], cwd=None)

        self.cli.remove_worktree("old-tree", force=True)
        self.mock_stream_exec.assert_called_with(
            ["worktree", "remove", "--force", "--", "old-tree"], cwd=None
        )

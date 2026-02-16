import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from gh_worktree.commands.remove import RemoveCommand
from gh_worktree.hooks import Hook


class StubContext:
    def __init__(self, project_dir):
        self.project_dir = project_dir

    @contextmanager
    def use(self, cwd):
        yield


class RemoveCommandTestCase(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_call__raises_when_missing(self):
        context = StubContext(self.tmp_path)
        runtime = SimpleNamespace(
            context=context,
            hooks=SimpleNamespace(fire=Mock()),
            git=SimpleNamespace(remove_worktree=Mock()),
        )

        command = RemoveCommand(runtime)

        with self.assertRaisesRegex(ValueError, "Worktree missing does not exist"):
            command("missing")

    def test_call__runs_hooks_and_git(self):
        project_dir = self.tmp_path / "project"
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

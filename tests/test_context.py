import tempfile
from pathlib import Path
from unittest import TestCase

from treefort.context import Context
from treefort.errors import ProjectNotFoundError


class ContextTestCase(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.context = Context()
        self.context.cwd = self.tmp_path

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_assert_within_project__success(self):
        (self.tmp_path / ".bare").mkdir()

        self.context.assert_within_project()

    def test_assert_within_project__failure(self):
        with self.assertRaises(ProjectNotFoundError):
            self.context.assert_within_project()

    def test_project_dir__cached(self):
        (self.tmp_path / ".bare").mkdir()

        project_dir = self.context.project_dir
        self.assertEqual(project_dir, self.tmp_path)

        project_dir_again = self.context.project_dir
        self.assertIs(project_dir_again, project_dir)

    def test_reset_properties(self):
        (self.tmp_path / ".bare").mkdir()

        _ = self.context.project_dir
        self.context.reset_properties()

        self.assertIsNone(self.context._cached_project_dir)

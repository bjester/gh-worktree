import tempfile
from pathlib import Path
from unittest import TestCase

from gh_worktree.utils import find_up


class FindUpTestCase(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_find_up_success(self):
        # Create a directory structure:
        # root/
        #   target_file
        #   subdir/
        #     subsubdir/
        root = self.tmp_path
        (root / "target_file").touch()
        subdir = root / "subdir"
        subdir.mkdir()
        subsubdir = subdir / "subsubdir"
        subsubdir.mkdir()

        # Test finding from subsubdir
        found_path = find_up("target_file", subsubdir)
        self.assertEqual(found_path, root / "target_file")

        # Test finding from root
        found_path = find_up("target_file", root)
        self.assertEqual(found_path, root / "target_file")

    def test_find_up_failure(self):
        # Create a directory structure without the target file
        root = self.tmp_path
        subdir = root / "subdir"
        subdir.mkdir()

        with self.assertRaisesRegex(RuntimeError, "Could not find non_existent_file"):
            find_up("non_existent_file", subdir)

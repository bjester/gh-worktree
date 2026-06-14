import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from treefort.context import Context, migrate_old_config


class MigrateOldConfigTestCase(TestCase):
    """Tests for the config migration functionality"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_migrate_old_config__returns_false_when_old_dir_not_exists(self):
        """Should return False when old directory doesn't exist"""
        old_dir = self.tmp_path / "old"
        new_dir = self.tmp_path / "new"

        result = migrate_old_config(old_dir, new_dir)

        self.assertFalse(result)
        self.assertFalse(new_dir.exists())

    def test_migrate_old_config__copies_files_successfully(self):
        """Should copy all files from old to new directory"""
        old_dir = self.tmp_path / "old"
        new_dir = self.tmp_path / "new"
        old_dir.mkdir()

        # Create test files
        (old_dir / "config.json").write_text('{"key": "value"}')
        (old_dir / "hooks").mkdir()
        (old_dir / "hooks" / "pre_init").write_text("#!/bin/bash\necho hello")
        (old_dir / "templates").mkdir()
        (old_dir / "templates" / "example.txt").write_text("template content")

        result = migrate_old_config(old_dir, new_dir)

        self.assertTrue(result)
        self.assertTrue(new_dir.exists())
        self.assertTrue((new_dir / "config.json").exists())
        self.assertEqual((new_dir / "config.json").read_text(), '{"key": "value"}')
        self.assertTrue((new_dir / "hooks").exists())
        self.assertTrue((new_dir / "hooks" / "pre_init").exists())
        self.assertEqual((new_dir / "hooks" / "pre_init").read_text(), "#!/bin/bash\necho hello")
        self.assertTrue((new_dir / "templates").exists())
        self.assertTrue((new_dir / "templates" / "example.txt").exists())

    def test_migrate_old_config__removes_old_directory_after_migration(self):
        """Should remove old directory after successful migration"""
        old_dir = self.tmp_path / "old"
        new_dir = self.tmp_path / "new"
        old_dir.mkdir()

        (old_dir / "config.json").write_text('{"key": "value"}')

        migrate_old_config(old_dir, new_dir)

        self.assertFalse(old_dir.exists())
        self.assertTrue(new_dir.exists())

    def test_migrate_old_config__cleans_up_empty_parent_gh_directory(self):
        """Should remove parent .gh directory if it becomes empty after migration"""
        gh_dir = self.tmp_path / ".gh"
        old_dir = gh_dir / "worktree"
        new_dir = self.tmp_path / ".treefort"
        old_dir.mkdir(parents=True)

        (old_dir / "config.json").write_text('{"key": "value"}')

        migrate_old_config(old_dir, new_dir)

        self.assertFalse(old_dir.exists())
        self.assertFalse(gh_dir.exists())
        self.assertTrue(new_dir.exists())

    def test_migrate_old_config__leaves_nonempty_parent_gh_directory(self):
        """Should leave parent .gh directory if it contains other items"""
        gh_dir = self.tmp_path / ".gh"
        old_dir = gh_dir / "worktree"
        other_dir = gh_dir / "other"
        new_dir = self.tmp_path / ".treefort"
        old_dir.mkdir(parents=True)
        other_dir.mkdir()

        (old_dir / "config.json").write_text('{"key": "value"}')

        migrate_old_config(old_dir, new_dir)

        self.assertFalse(old_dir.exists())
        self.assertTrue(gh_dir.exists())
        self.assertTrue(other_dir.exists())
        self.assertTrue(new_dir.exists())

    def test_migrate_old_config__preserves_file_permissions(self):
        """Should preserve file permissions during migration"""
        import stat

        old_dir = self.tmp_path / "old"
        new_dir = self.tmp_path / "new"
        old_dir.mkdir()

        # Create an executable file
        hook_file = old_dir / "executable_script"
        hook_file.write_text("#!/bin/bash\necho hello")
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)

        migrate_old_config(old_dir, new_dir)

        new_hook_file = new_dir / "executable_script"
        self.assertTrue(new_hook_file.exists())
        # Check that execute permission is preserved
        self.assertTrue(new_hook_file.stat().st_mode & stat.S_IEXEC)


class ContextMigrationTestCase(TestCase):
    """Tests for Context class migration behavior"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.context = Context()
        self.context.cwd = self.tmp_path

    def tearDown(self):
        self.tmp_dir.cleanup()

    @patch("treefort.context.find_up")
    @patch("treefort.context.Path.home")
    def test_migrate__migrates_from_old_location(self, mock_home, mock_find_up):
        """Should migrate from .gh/worktree to ~/.treefort when accessing global config"""
        # Setup mock home directory
        home_dir = self.tmp_path / "home"
        home_dir.mkdir()
        mock_home.return_value = home_dir

        # Setup old .gh/worktree location
        old_gh_dir = home_dir / ".gh"
        old_gh_dir.mkdir()
        old_config_dir = old_gh_dir / "worktree"
        old_config_dir.mkdir()
        (old_config_dir / "config.json").write_text('{"type": "global", "test": "value"}')

        # Mock find_up to return the .gh directory
        mock_find_up.return_value = old_gh_dir

        # run
        self.context.migrate()

        # Verify migration occurred
        new_config_dir = home_dir / ".treefort"
        self.assertTrue(new_config_dir.exists())
        self.assertTrue((new_config_dir / "config.json").exists())
        self.assertEqual(
            (new_config_dir / "config.json").read_text(),
            '{"type": "global", "test": "value"}',
        )
        # Old directory should be removed
        self.assertFalse(old_config_dir.exists())
        self.assertFalse(old_gh_dir.exists())

    @patch("treefort.context.find_up")
    @patch("treefort.context.Path.home")
    def test_migrate__no_migration_when_no_old_config(self, mock_home, mock_find_up):
        """Should not migrate when old config doesn't exist"""
        # Setup mock home directory
        home_dir = self.tmp_path / "home"
        home_dir.mkdir()
        mock_home.return_value = home_dir

        # Mock find_up to raise AncestorNotFoundError (no .gh found)
        from treefort.errors import AncestorNotFoundError

        mock_find_up.side_effect = AncestorNotFoundError("Not found")

        # run
        self.context.migrate()
        result = self.context.global_config_dir

        # Should return new location without migration
        expected = home_dir / ".treefort"
        self.assertEqual(result, expected)

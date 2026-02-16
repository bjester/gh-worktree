import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from gh_worktree.commands.install import InstallCommand


class InstallCommandTestCase(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.runtime = SimpleNamespace()
        self.command = InstallCommand(self.runtime)

    def tearDown(self):
        self.tmp_dir.cleanup()

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__installs_as_gh_extension_with_default_name(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
    ):
        self.command(gh_ext=True)

        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_copy.assert_called_once_with(Path("/usr/bin/gh-worktree"), expected_target)

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__installs_as_gh_extension_with_custom_alias(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
    ):
        self.command(alias="wktr", gh_ext=True)

        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-wktr"
            / "gh-wktr"
        )
        mock_copy.assert_called_once_with(Path("/usr/bin/gh-worktree"), expected_target)

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__installs_as_gh_extension_and_adds_gh_prefix(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
    ):
        self.command(alias="worktree", gh_ext=True)

        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_copy.assert_called_once_with(Path("/usr/bin/gh-worktree"), expected_target)

    @patch.dict(os.environ, {"PATH": f"{Path.home()}/.local/bin:/usr/bin"})
    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__installs_to_path_bin(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
    ):
        self.command(path_bin=True)

        expected_target = Path.home() / ".local" / "bin" / "gh-worktree"
        mock_copy.assert_called_once_with(Path("/usr/bin/gh-worktree"), expected_target)

    @patch.dict(os.environ, {"PATH": f"{Path.home()}/.local/bin:/usr/bin"})
    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__installs_to_path_bin_with_custom_alias(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
    ):
        self.command(alias="wktr", path_bin=True)

        expected_target = Path.home() / ".local" / "bin" / "wktr"
        mock_copy.assert_called_once_with(Path("/usr/bin/gh-worktree"), expected_target)

    @patch.dict(os.environ, {"PATH": "/usr/bin:/usr/local/bin"})
    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("builtins.print")
    def test_call__fails_when_no_suitable_path_directory_found(self, mock_print):
        with self.assertRaises(SystemExit) as cm:
            self.command(path_bin=True)

        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_called_with(
            "Could not find a suitable user binary directory in your PATH."
        )

    @patch("sys.argv", ["/home/user/gh-worktree/src/gh_worktree/main.py"])
    @patch("os.symlink")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__uses_symlink_when_running_from_source(
        self, mock_print, mock_is_symlink, mock_exists, mock_mkdir, mock_symlink
    ):
        self.command(gh_ext=True)

        expected_source = Path("/home/user/gh-worktree/src/gh_worktree/main.py")
        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_symlink.assert_called_once_with(expected_source, expected_target)

    @patch("sys.argv", ["/home/user/gh-worktree/.venv/bin/gh-worktree"])
    @patch("os.symlink")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__uses_symlink_when_running_from_venv(
        self, mock_print, mock_is_symlink, mock_exists, mock_mkdir, mock_symlink
    ):
        self.command(gh_ext=True)

        expected_source = Path("/home/user/gh-worktree/.venv/bin/gh-worktree")
        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_symlink.assert_called_once_with(expected_source, expected_target)

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__uses_copy_for_compiled_binary(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
    ):
        self.command(gh_ext=True)

        expected_source = Path("/usr/bin/gh-worktree")
        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_copy.assert_called_once_with(expected_source, expected_target)
        mock_chmod.assert_called_once()

    @patch("sys.argv", ["/usr/bin/gh-worktree.pex"])
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__uses_copy_for_pex_file(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
    ):
        self.command(gh_ext=True)

        expected_source = Path("/usr/bin/gh-worktree.pex")
        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_copy.assert_called_once_with(expected_source, expected_target)

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("builtins.input", return_value="1")
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__prompts_user_when_no_options_specified_and_chooses_gh_ext(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
        mock_input,
    ):
        self.command()

        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_copy.assert_called_once_with(Path("/usr/bin/gh-worktree"), expected_target)

    @patch.dict(os.environ, {"PATH": f"{Path.home()}/.local/bin:/usr/bin"})
    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("builtins.input", return_value="2")
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__prompts_user_when_no_options_specified_and_chooses_path_bin(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
        mock_input,
    ):
        self.command()

        expected_target = Path.home() / ".local" / "bin" / "gh-worktree"
        mock_copy.assert_called_once_with(Path("/usr/bin/gh-worktree"), expected_target)

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("builtins.input", return_value="3")
    @patch("sys.exit")
    def test_call__exits_when_invalid_choice(self, mock_exit, mock_input):
        self.command()

        mock_exit.assert_called_once_with(1)

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__exits_when_target_exists_without_force(
        self, mock_print, mock_is_symlink, mock_exists
    ):
        with self.assertRaises(SystemExit) as cm:
            self.command(gh_ext=True)

        self.assertEqual(cm.exception.code, 1)
        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_print.assert_called_with(
            f"Path already exists, use --force to overwrite: {expected_target}"
        )

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.is_symlink", return_value=True)
    @patch("builtins.print")
    def test_call__exits_when_target_is_symlink_without_force(
        self, mock_print, mock_is_symlink, mock_exists
    ):
        with self.assertRaises(SystemExit) as cm:
            self.command(gh_ext=True)

        self.assertEqual(cm.exception.code, 1)
        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_print.assert_called_with(
            f"Path already exists, use --force to overwrite: {expected_target}"
        )

    @patch("sys.argv", ["/usr/bin/gh-worktree"])
    @patch("shutil.copy")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.is_symlink", return_value=False)
    @patch("builtins.print")
    def test_call__overwrites_when_target_exists_with_force(
        self,
        mock_print,
        mock_is_symlink,
        mock_exists,
        mock_unlink,
        mock_stat,
        mock_chmod,
        mock_mkdir,
        mock_copy,
    ):
        self.command(gh_ext=True, force=True)

        expected_target = (
            Path.home()
            / ".local"
            / "share"
            / "gh"
            / "extensions"
            / "gh-worktree"
            / "gh-worktree"
        )
        mock_unlink.assert_called_once_with(True)
        mock_copy.assert_called_once_with(Path("/usr/bin/gh-worktree"), expected_target)

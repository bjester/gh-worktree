import glob
import hashlib
import os
import shutil
import stat
from unittest import mock
from unittest import TestCase

import pytest
from gh_worktree.context import Context
from gh_worktree.hooks import Hook
from gh_worktree.hooks import HookExists
from gh_worktree.hooks import Hooks


class HooksTestCase(TestCase):
    @pytest.fixture(autouse=True)
    def prepare_fixture(self, tmp_path):
        self.tmp_path = tmp_path

    def setUp(self):
        self.context = Context()
        self.context.cwd = str(self.tmp_path)
        self.hooks_path = self.tmp_path / ".gh" / "worktree" / "hooks"
        os.makedirs(self.tmp_path / ".bare")
        os.makedirs(self.context.config_dir)
        self.hooks_path.mkdir()

        self.hooks = Hooks(self.context)

    def tearDown(self):
        for file_path in glob.glob("*", root_dir=self.tmp_path):
            shutil.rmtree(os.path.join(self.tmp_path, file_path))

    @mock.patch("gh_worktree.hooks.input")
    def test_check_allowed__existing_hook(self, mock_input):
        global_config = self.context.get_global_config()

        hook_file = self.hooks_path / Hook.pre_init.name
        hook_file.write_bytes(b"echo ok")
        checksum = hashlib.sha256(hook_file.read_bytes()).hexdigest()

        global_config.allow_hook(str(hook_file), checksum)
        self.context.set_config(global_config)

        self.assertTrue(self.hooks._check_allowed(str(hook_file)))

        mock_input.assert_not_called()
        global_config = self.context.get_global_config()
        self.assertEqual(global_config.allowed_hooks[str(hook_file)], checksum)

    @mock.patch("gh_worktree.hooks.input")
    def test_check_allowed__prompts_and_saves(self, mock_input):
        hook_file = self.hooks_path / Hook.pre_init.name
        hook_file.write_bytes(b"echo ok")
        checksum = hashlib.sha256(hook_file.read_bytes()).hexdigest()

        mock_input.return_value = "y"

        self.assertTrue(self.hooks._check_allowed(str(hook_file)))

        mock_input.assert_called_once()
        global_config = self.context.get_global_config()
        self.assertEqual(global_config.allowed_hooks[str(hook_file)], checksum)

    @mock.patch("gh_worktree.hooks.Hooks._check_allowed")
    @mock.patch("gh_worktree.hooks.stream_exec")
    def test_fire__allowed(self, mock_stream_exec, mock_check_allowed):
        hook_file = self.hooks_path / Hook.pre_init.name
        hook_file.write_bytes(b"echo ok")
        # Make the hook file executable
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)

        mock_check_allowed.return_value = True
        mock_stream_exec.return_value = 0

        self.assertTrue(self.hooks.fire(Hook.pre_init, "arg1"))
        mock_stream_exec.assert_called_once_with(
            [str(hook_file), "arg1"], cwd=str(self.tmp_path)
        )

    @mock.patch("gh_worktree.hooks.Hooks._check_allowed")
    @mock.patch("gh_worktree.hooks.stream_exec")
    def test_fire__not_executable(self, mock_stream_exec, mock_check_allowed):
        hook_file = self.hooks_path / Hook.pre_init.name
        hook_file.write_bytes(b"echo ok")
        hook_file.chmod(stat.S_IREAD)

        mock_check_allowed.return_value = True
        mock_stream_exec.return_value = 0

        self.assertFalse(self.hooks.fire(Hook.pre_init, "arg1"))
        mock_stream_exec.assert_not_called()

    @mock.patch("gh_worktree.hooks.Hooks._check_allowed")
    @mock.patch("gh_worktree.hooks.stream_exec")
    def test_fire__disallowed(self, mock_stream_exec, mock_check_allowed):
        hook_file = self.hooks_path / Hook.pre_init.name
        hook_file.write_bytes(b"echo ok")
        # Make the hook file executable
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)

        mock_check_allowed.return_value = False
        mock_stream_exec.return_value = 0

        self.assertFalse(self.hooks.fire(Hook.pre_init, "arg1"))
        mock_stream_exec.assert_not_called()

    def test_add(self):
        with self.hooks.add(Hook.pre_init) as f:
            f.write("echo ok")

        hook_file = self.hooks_path / Hook.pre_init.name
        self.assertTrue(hook_file.exists())
        self.assertEqual(hook_file.read_text(), "echo ok")
        self.assertTrue(os.access(hook_file, os.X_OK))

    def test_add__existing(self):
        hook_file = self.hooks_path / Hook.pre_init.name
        hook_file.write_bytes(b"echo ok")

        with self.assertRaises(HookExists):
            with self.hooks.add(Hook.pre_init) as f:
                f.write("echo ok")

import hashlib
import os
import stat

import pytest

from gh_worktree.config import GlobalConfig
from gh_worktree.hooks import Hook, Hooks


class StubContext:
    def __init__(self, global_config, global_config_dir, config_dir, cwd):
        self._global_config = global_config
        self.global_config_dir = global_config_dir
        self.config_dir = config_dir
        self.cwd = cwd
        self.set_config_called = False

    def get_global_config(self):
        return self._global_config

    def set_config(self, config):
        self.set_config_called = True


def test_check_allowed_existing_hook(tmp_path, monkeypatch):
    hook_file = tmp_path / "pre_init"
    hook_file.write_bytes(b"echo ok")
    checksum = hashlib.sha256(hook_file.read_bytes()).hexdigest()

    global_config = GlobalConfig()
    global_config.allow_hook(str(hook_file), checksum)
    context = StubContext(global_config, str(tmp_path), str(tmp_path), str(tmp_path))

    monkeypatch.setattr(
        "builtins.input", lambda _: pytest.fail("input should not be called")
    )

    hooks = Hooks(context)
    assert hooks._check_allowed(str(hook_file)) is True
    assert context.set_config_called is False


def test_check_allowed_prompts_and_saves(tmp_path, monkeypatch):
    hook_file = tmp_path / "pre_init"
    hook_file.write_bytes(b"echo ok")

    global_config = GlobalConfig()
    context = StubContext(global_config, str(tmp_path), str(tmp_path), str(tmp_path))

    monkeypatch.setattr("builtins.input", lambda _: "y")

    hooks = Hooks(context)
    assert hooks._check_allowed(str(hook_file)) is True
    assert context.set_config_called is True
    assert str(hook_file) in global_config.allowed_hooks


def test_fire_runs_hook_when_allowed(tmp_path, monkeypatch):
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    hook_file = hooks_dir / Hook.pre_init.name
    hook_file.write_text("#!/bin/sh\n")
    # Make the hook file executable
    hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    context = StubContext(
        GlobalConfig(), str(tmp_path), str(project_dir), str(tmp_path)
    )
    hooks = Hooks(context)

    monkeypatch.setattr(hooks, "_check_allowed", lambda _: True)

    calls = []

    def fake_stream_exec(command, cwd):
        calls.append((command, cwd))
        return 0

    monkeypatch.setattr("gh_worktree.hooks.stream_exec", fake_stream_exec)

    assert hooks.fire(Hook.pre_init, "arg1") is True
    assert calls == [([str(hook_file), "arg1"], str(tmp_path))]

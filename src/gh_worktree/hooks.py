import hashlib
import os
import stat
from contextlib import contextmanager
from enum import Enum

from gh_worktree.context import Context
from gh_worktree.operator import ConfigOperator
from gh_worktree.utils import stream_exec


class Hook(Enum):
    pre_init = 1
    post_init = 2
    pre_checkout = 3
    post_checkout = 4
    pre_create = 5
    post_create = 6
    pre_remove = 7
    post_remove = 8

    @property
    def git_path(self):
        return f".gh/worktree/hooks/{self.name}"


class HookExists(Exception):
    pass


class Hooks(ConfigOperator):
    def __init__(self, context: Context):
        super().__init__(context)
        self.dir_name = "hooks"

    def fire(self, hook: Hook, *args, skip_project: bool = False) -> bool:
        fired = False

        for hooks_dir in self.iter_config_dirs(skip_project=skip_project):
            hook_file = hooks_dir / hook.name
            if not hook_file.exists():
                continue

            # Ensure the hook file is executable
            hook_file_str = str(hook_file)
            if not os.access(hook_file_str, os.X_OK):
                print(f"Hook {hook_file_str} is not executable. Skipping.")
                continue

            if not self._check_allowed(hook_file_str):
                print(f"Hook {hook_file_str} is not allowed to run. Skipping.")
                continue

            fired = True
            command_args = [hook_file_str, *[str(arg) for arg in args]]
            return_status = stream_exec(command_args, cwd=self.context.cwd)
            if return_status != 0:
                raise RuntimeError(
                    f"Hook {hook.name} failed with exit code {return_status}"
                )
        return fired

    def _check_allowed(self, hook_file: str) -> bool:
        with open(hook_file, "rb") as f:
            content = f.read()
        checksum = hashlib.sha256(content).hexdigest()

        global_config = self.context.get_global_config()
        allowed_hooks = global_config.allowed_hooks

        if hook_file in allowed_hooks and allowed_hooks[hook_file] == checksum:
            return True

        print(f"New hook found: {hook_file}")
        response = input("Do you want to allow this hook to run? (y/N): ")
        if response.lower() == "y":
            global_config.allow_hook(hook_file, checksum)
            self.context.set_config(global_config)
            return True

        return False

    @contextmanager
    def add(self, hook: Hook):
        hooks_dir = self.context.config_dir / "hooks"
        hook_file = hooks_dir / hook.name
        hooks_dir.mkdir(parents=True, exist_ok=True)

        if hook_file.exists():
            raise HookExists(f"Hook {hook_file} already exists.")

        # copy it to config
        with hook_file.open("w", encoding="utf-8", newline="\n") as f:
            yield f

        # allow exec
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)

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
            hook_file = os.path.join(hooks_dir, hook.name)
            if not os.path.exists(hook_file):
                continue

            # Ensure the hook file is executable
            if not os.access(hook_file, os.X_OK):
                print(f"Hook {hook_file} is not executable. Skipping.")
                continue

            if not self._check_allowed(hook_file):
                print(f"Hook {hook_file} is not allowed to run. Skipping.")
                continue

            fired = True
            return_status = stream_exec([hook_file, *args], cwd=self.context.cwd)
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
        hooks_dir = os.path.join(self.context.config_dir, "hooks")
        hook_file = os.path.join(hooks_dir, hook.name)
        os.makedirs(hooks_dir, exist_ok=True)

        if os.path.exists(hook_file):
            raise HookExists(f"Hook {hook_file} already exists.")

        # copy it to config
        with open(hook_file, "w", newline="\n") as f:
            yield f

        # allow exec
        os.chmod(hook_file, os.stat(hook_file).st_mode | stat.S_IEXEC)

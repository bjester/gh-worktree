import hashlib
import os
import stat
from enum import Enum

from gh_worktree.context import Context
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


class Hooks(object):
    def __init__(self, context: Context):
        self.context = context

    def fire(self, hook: Hook, *args, skip_project: bool = False) -> bool:
        fired = False
        configs = [self.context.global_config_dir]
        if not skip_project:
            configs.append(self.context.config_dir)

        for config_dir in configs:
            hooks_dir = os.path.join(config_dir, "hooks")
            if not os.path.exists(hooks_dir):
                continue
            hook_file = os.path.join(hooks_dir, hook.name)
            if not os.path.exists(hook_file):
                continue

            # Ensure the hook file is executable
            if not os.access(hook_file, os.X_OK):
                # Try to make it executable if it's owned by the user
                try:
                    st = os.stat(hook_file)
                    os.chmod(hook_file, st.st_mode | stat.S_IEXEC)
                except OSError:
                    print(
                        f"Hook {hook_file} is not executable and could not be made executable. Skipping."
                    )
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

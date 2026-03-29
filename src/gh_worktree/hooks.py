import hashlib
import os
import stat
from contextlib import contextmanager
from enum import Enum

from gh_worktree.context import Context
from gh_worktree.operator import ConfigOperator
from gh_worktree.utils import COLOR_RESET
from gh_worktree.utils import COLOR_YELLOW
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
    """
    Encapsulates operations for managing and executing hooks in the configuration
    system, such as firing hooks, checking their permissions, and adding new hooks.

    This class is designed to integrate with a configuration directory structure,
    allowing for the execution of hooks with appropriate validation steps. Hooks
    are only executed if they're checksum has been registered as allowed.
    """

    def __init__(self, context: Context):
        super().__init__(context)
        self.dir_name = "hooks"

    def fire(
        self,
        hook: Hook,
        *args,
        skip_project: bool = False,
        bypass_allowlist: bool = False,
    ) -> bool:
        """
        Fire a hook with given arguments.
        :param hook: The hook to fire
        :param args: The arguments to pass to the hook
        :param skip_project: Whether to skip the project-level hooks
        :param bypass_allowlist: Whether to bypass the allowlist check
        :return: Whether the hook was fired
        """
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

            if not self._check_allowed(
                hook_file_str, bypass_allowlist=bypass_allowlist
            ):
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

    def _check_allowed(self, hook_file: str, bypass_allowlist: bool = False) -> bool:
        """
        Check if a hook is allowed to run.
        :param hook_file: The path to the hook file
        :param bypass_allowlist: Whether to bypass the allowlist check
        :return: Whether the hook is allowed to run
        """
        with open(hook_file, "rb") as f:
            content = f.read()
        checksum = hashlib.sha256(content).hexdigest()

        global_config = self.context.get_global_config()
        allowed_hooks = global_config.allowed_hooks

        if hook_file in allowed_hooks and allowed_hooks[hook_file] == checksum:
            return True

        print(f"New/modified hook found: {hook_file}")
        if bypass_allowlist:
            print(
                f"{COLOR_YELLOW}WARNING! Bypassing allowlist check for {hook_file}{COLOR_RESET}"
            )
            return True

        response = input("Do you want to allow this hook to run? (y/N): ")
        if response.lower() == "y":
            global_config.allow_hook(hook_file, checksum)
            self.context.set_config(global_config)
            return True

        return False

    @contextmanager
    def add(self, hook: Hook):
        """
        Add a new hook to the worktree configuration and yields a file handle to write its contents.
        :param hook: The hook to add
        """
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

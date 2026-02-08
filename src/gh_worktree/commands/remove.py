import os.path

from gh_worktree.command import Command
from gh_worktree.hooks import Hook


class RemoveCommand(Command):
    def __call__(self, worktree_name: str, force: bool = False):
        project_dir = self._context.project_dir
        if not os.path.exists(os.path.join(project_dir, worktree_name)):
            raise ValueError(f"Worktree {worktree_name} does not exist")

        with self._context.use(project_dir):
            self._runtime.hooks.fire(Hook.pre_remove, worktree_name)
            self._runtime.git.remove_worktree(worktree_name, force=force)
            self._runtime.hooks.fire(Hook.post_remove, worktree_name)

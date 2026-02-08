import os.path

from gh_worktree.command import Command
from gh_worktree.hooks import Hook


class RemoveCommand(Command):
    """Remove a worktree from the current project"""

    _name = "remove"
    _aliases = ["rm"]

    def __call__(self, worktree_name: str, force: bool = False):
        """
        Remove a worktree from the current project that was added with `create` or `checkout`
        :param worktree_name: The name of the worktree to remove
        :param force: Whether to force the removal of the worktree, if it's unmerged
        """
        project_dir = self._context.project_dir
        if not os.path.exists(os.path.join(project_dir, worktree_name)):
            raise ValueError(f"Worktree {worktree_name} does not exist")

        with self._context.use(project_dir):
            self._runtime.hooks.fire(Hook.pre_remove, worktree_name)
            self._runtime.git.remove_worktree(worktree_name, force=force)
            self._runtime.hooks.fire(Hook.post_remove, worktree_name)

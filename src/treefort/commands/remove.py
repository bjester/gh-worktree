from treefort.command import Command
from treefort.errors import CommandError, WorktreeNotFoundError
from treefort.hooks import Hook
from treefort.utils import normalize_worktree_name


class RemoveCommand(Command):
    """Remove a worktree from the current project"""

    _name = "remove"
    _aliases = ["rm"]

    def __call__(
        self,
        worktree_name: str,
        force: bool = False,
        yes: bool = False,
        delete_branch: bool = False,
    ):
        """
        Remove a worktree from the current project that was added with `create` or `checkout`.

        If git detects the worktree has commits that are unmerged, then it will refuse to delete it.
        You may use `--force` to passthrough `--force` to git and force the worktree's deletion.

        Examples:
            treefort remove testing-create
            treefort remove testing-create --force
            treefort remove testing-create --delete-branch

        :param worktree_name: The name of the worktree to remove
        :param force: Whether to force the removal of the worktree, if it's unmerged
        :param yes: Perform any action automatically without asking
            (execute new or modified hooks)
        :param delete_branch: Whether to also delete the local Git branch
            associated with the worktree (branch name matches worktree name)
        """
        project_dir = self._context.project_dir
        if not (project_dir / worktree_name).exists():
            raise WorktreeNotFoundError(f"Worktree {worktree_name} does not exist")

        normalized_name = normalize_worktree_name(worktree_name)

        with self._context.use(project_dir):
            self._runtime.hooks.fire(
                Hook.pre_remove, worktree_name, normalized_name, bypass_allowlist=yes
            )
            self._runtime.git.remove_worktree(worktree_name, force=force)

            if delete_branch:
                try:
                    self._runtime.git.delete_branch(worktree_name, force=force)
                except CommandError as e:
                    self._logger.warning(f"Failed to delete branch '{worktree_name}': {e}")

            self._runtime.hooks.fire(
                Hook.post_remove, worktree_name, normalized_name, bypass_allowlist=yes
            )

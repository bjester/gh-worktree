from pathlib import Path

from treefort.command import Command
from treefort.errors import CommandError
from treefort.hooks import Hook
from treefort.utils import normalize_worktree_name


class PruneCommand(Command):
    """Prune worktrees whose associated PRs have been merged"""

    _name = "prune"

    def __call__(self, force: bool = False, yes: bool = False):
        """
        Prune worktrees whose associated PRs have been merged.

        This command identifies worktrees linked to merged PRs and removes
        both the worktree directory and the local Git branch.

        Examples:
            treefort prune
            treefort prune --yes
            treefort prune --force --yes

        :param force: Whether to force the removal of the worktree and branch,
            bypassing git safety checks
        :param yes: Perform any action automatically without asking (execute new or modified hooks)
        """
        self._context.assert_within_project()

        pruned_count = 0
        failed_count = 0

        for worktree_name, branch_name in self._iter_worktrees():
            if not yes:
                response = input(
                    f"Remove worktree '{worktree_name}' and branch '{branch_name}'? (y/N): "
                )
                if response.lower() != "y":
                    self._logger.info(f"Skipping '{worktree_name}'")
                    continue

            if self._do_prune(worktree_name, branch_name, force, yes):
                pruned_count += 1
            else:
                failed_count += 1

        if pruned_count == 0 and failed_count == 0:
            self._logger.info("No merged PR worktrees found to prune.")
        else:
            self._logger.info(f"Pruning complete: {pruned_count} pruned, {failed_count} failed.")

    def _iter_worktrees(self):
        """
        Filter worktrees and search for matching PRs, yield candidates for pruning.
        """
        project_dir = self._context.project_dir
        config = self._context.get_config()

        worktrees = self._runtime.git.list_worktrees()

        for wt in worktrees:
            if wt.get("is_bare") or Path(wt["path"]).resolve() == project_dir.resolve():
                continue

            branch_ref = wt.get("branch")
            if not branch_ref or not branch_ref.startswith("refs/heads/"):
                continue

            branch_name = branch_ref.removeprefix("refs/heads/")
            worktree_name = Path(wt["path"]).name

            pr_infos = self._runtime.gh.merged_pr_by_head(
                branch_name, owner_repo=f"{config.owner}/{config.name}"
            )

            if not pr_infos:
                continue

            # Safety check: ensure local branch head matches the merged PR head
            try:
                local_head = self._runtime.git.get_branch_head(branch_name)
            except CommandError as e:
                self._logger.warning(f"Skipping '{worktree_name}': could not get branch head ({e})")
                continue

            pr_info = next((_pr for _pr in pr_infos if _pr.get("headRefOid") == local_head), None)

            if not pr_info:
                pr_heads = [pr["headRefOid"][:8] for pr in pr_infos if pr.get("headRefOid")]
                self._logger.warning(
                    f"Skipping '{worktree_name}': local branch head ({local_head[:8]}) does not "
                    f"match any merged PR head(s) ({','.join(pr_heads)}). "
                    "The branch may have been reused."
                )
                continue

            self._logger.info(f"Found merged PR for worktree '{worktree_name}':")
            self._logger.info(f"  PR #{pr_info['number']}: {pr_info['title']}")
            self._logger.info(f"  URL: {pr_info['url']}")

            yield worktree_name, branch_name

    def _do_prune(self, worktree_name: str, branch_name: str, force: bool, yes: bool):
        """
        Executes the prune operation, firing the hooks before and after.
        """
        project_dir = self._context.project_dir

        try:
            normalized_name = normalize_worktree_name(worktree_name)
            with self._context.use(project_dir):
                self._runtime.hooks.fire(
                    Hook.pre_remove, worktree_name, normalized_name, bypass_allowlist=yes
                )

                self._runtime.git.remove_worktree(worktree_name, force=force)
                try:
                    self._runtime.git.delete_branch(branch_name, force=force)
                except CommandError as e:
                    self._logger.warning(f"Failed to delete branch '{branch_name}': {e}")

                self._runtime.hooks.fire(
                    Hook.post_remove, worktree_name, normalized_name, bypass_allowlist=yes
                )

            self._logger.info(f"Successfully pruned '{worktree_name}'")
            return True
        except CommandError as e:
            self._logger.error(f"Failed to prune '{worktree_name}': {e}")
            return False

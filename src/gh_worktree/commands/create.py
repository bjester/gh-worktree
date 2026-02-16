from typing import Optional

from gh_worktree.command import Command
from gh_worktree.hooks import Hook


class CreateCommand(Command):
    _name = "create"

    def __call__(self, worktree_name: str, *base_ref: Optional[str]):
        """
        Create a new worktree in the current project.

        This will add a new directory to your project directory with the name provided to
        `worktree_name`. By default, the worktree branch will be based off the default GitHub
        repository branch. To base it off another branch, you may use specify it as the second
        argument. If the branch you want to base off contains a slash (`branch/name`), you must also
        specify prefix it with the remote name and a slash, e.g. `remote/branch/name`.

        Examples:
            gh-worktree create testing-create
            gh-worktree create testing-create main
            gh-worktree create testing-create upstream/main
            gh-worktree create testing-create upstream/some/other/branch

        :param worktree_name: The name of the worktree
        :param base_ref: The base reference to create the worktree from
        """
        base_ref = base_ref[0] if base_ref else None
        self._context.assert_within_project()
        git_remote_name = None

        if base_ref is None:
            project_config = self._context.get_config()
            base_ref = project_config.default_branch
        elif "/" in base_ref:
            git_remote_name, base_ref = base_ref.split("/", 1)

        if git_remote_name is None:
            git_remote = self._runtime.get_remote()
            git_remote_name = git_remote.name

        # self._runtime.git.fetch(git_remote_name, f"{base_ref}:{base_ref}")
        self._runtime.git.fetch(git_remote_name)

        with self._context.use(self._context.project_dir):
            self._runtime.hooks.fire(
                Hook.pre_create, worktree_name, f"{git_remote_name}/{base_ref}"
            )
            self._runtime.git.add_worktree(
                worktree_name, f"{git_remote_name}/{base_ref}"
            )
            self._runtime.templates.copy(worktree_name)
            self._runtime.hooks.fire(
                Hook.post_create, worktree_name, f"{git_remote_name}/{base_ref}"
            )

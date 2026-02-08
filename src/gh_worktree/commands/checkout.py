from gh_worktree.command import Command
from gh_worktree.hooks import Hook


class CheckoutCommand(Command):
    _name = "checkout"

    def __call__(self, branch_or_pr: str):
        """Checkout an existing branch or PR as a worktree
        :param branch_or_pr: The branch, PR number, or PR URL to create as a worktree
        """
        self._context.assert_within_project()
        config = self._context.get_config()

        worktree_name = branch_or_pr
        pr_number = None
        default_remote = self._runtime.get_remote()
        if not default_remote:
            raise ValueError("Couldn't determine default remote")

        if branch_or_pr.isdigit():
            pr_number = branch_or_pr
        elif branch_or_pr.startswith(config.url):
            pull, pr_number = (
                branch_or_pr.replace(config.url, "").lstrip("/").split("/")
            )
            if pull != "pull" or not pr_number.isdigit():
                raise AssertionError("Invalid pull request URL")

        if pr_number:
            pr_status = self._runtime.gh.pr_status(pr_number)
            worktree_name = pr_status["headRefName"]
            default_remote = pr_status["headRepositoryOwner"]["login"]
            self._runtime.git.fetch(
                default_remote.name, f"pull/{pr_number}/head:{worktree_name}"
            )

        with self._context.use(self._context.project_dir):
            self._runtime.hooks.fire(
                Hook.pre_checkout, worktree_name, f"{default_remote}/{worktree_name}"
            )
            self._runtime.git.open_worktree(worktree_name)
            self._runtime.hooks.fire(
                Hook.post_checkout, worktree_name, f"{default_remote}/{worktree_name}"
            )

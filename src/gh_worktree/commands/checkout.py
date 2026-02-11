from gh_worktree.command import Command
from gh_worktree.hooks import Hook


class CheckoutCommand(Command):
    _name = "checkout"

    def __call__(self, branch_or_pr: str):  # noqa: C901
        """Checkout an existing branch or PR as a worktree
        :param branch_or_pr: The branch, PR number, or PR URL to create as a worktree
        """
        self._context.assert_within_project()
        config = self._context.get_config()

        branch_or_pr = str(branch_or_pr)
        worktree_name = None
        pr_number = None
        default_remote = self._runtime.get_remote()
        if not default_remote:
            raise AssertionError("Couldn't determine default remote")

        owner_name = config.owner
        remote_name = default_remote.name

        if branch_or_pr.isdigit():
            pr_number = branch_or_pr
        elif branch_or_pr.startswith("https://github.com"):
            if branch_or_pr.startswith(config.url):
                pull, pr_number = (
                    branch_or_pr.replace(config.url, "").lstrip("/").split("/")
                )
            else:
                owner_name, repo, pull, pr_number = branch_or_pr.replace(
                    "https://github.com/", ""
                ).split("/")
                # assumes the remote name is the same as the github owner
                remote_name = owner_name
                if repo != config.name:
                    raise AssertionError(
                        f"Pull request appears to be for '{repo}' instead of '{config.name}'"
                    )

            if pull != "pull" or not pr_number.isdigit():
                raise AssertionError("Invalid pull request URL")
        elif branch_or_pr.startswith("https"):
            raise AssertionError("Invalid pull request URL")
        else:
            names = branch_or_pr.split("/", 1)
            if len(names) > 1:
                remote_name, worktree_name = names
            else:
                worktree_name = names[0]

        if pr_number:
            pr_status = self._runtime.gh.pr_status(
                pr_number, owner_repo=f"{owner_name}/{config.name}"
            )
            worktree_name = pr_status["headRefName"]
            self._runtime.git.fetch(
                remote_name, f"pull/{pr_number}/head:{worktree_name}"
            )
        elif worktree_name:
            # TODO: detect if it's local only
            try:
                self._runtime.git.fetch(remote_name, f"{worktree_name}:{worktree_name}")
            except RuntimeError:
                print("Ignoring git fetch error, attempting to open worktree")
                pass

        if not worktree_name:
            raise AssertionError("Could not determine worktree name")

        with self._context.use(self._context.project_dir):
            self._runtime.hooks.fire(
                Hook.pre_checkout, worktree_name, f"{default_remote}/{worktree_name}"
            )
            self._runtime.git.open_worktree(worktree_name)
            self._runtime.hooks.fire(
                Hook.post_checkout, worktree_name, f"{default_remote}/{worktree_name}"
            )

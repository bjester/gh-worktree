import re
from functools import cached_property
from typing import Optional

from gh_worktree.command import Command
from gh_worktree.hooks import Hook
from gh_worktree.runtime import Runtime


URL_RE = re.compile(r"^https://github\.com/[a-z0-9-]+/[\w.-]+/pull/\d+$", re.IGNORECASE)
BRANCH_RE = re.compile(r"^[\w.-/]+$", re.IGNORECASE)


class CheckoutInput(object):
    """Checkout command input abstraction"""

    def __init__(
        self, runtime: Runtime, branch_or_pr: str, remote_name: Optional[str] = None
    ):
        self.runtime = runtime
        self.branch_or_pr = branch_or_pr
        self.remote_name = remote_name

    def validate(self):
        if (
            not self.branch_or_pr.isdigit()
            and not URL_RE.match(self.branch_or_pr)
            and not BRANCH_RE.match(self.branch_or_pr)
        ):
            raise ValueError(
                "Couldn't parse input. Must be branch name, PR number or PR URL."
            )

        if self.remote_name is not None and (
            self.branch_or_pr.isdigit() or URL_RE.match(self.branch_or_pr)
        ):
            raise ValueError("Remote name isn't allowed with PR number or PR URL.")

    @cached_property
    def owner(self) -> str:
        """The Github owner of the repository"""
        config = self.runtime.context.get_config()
        if (
            self.branch_or_pr.isdigit()
            or self.branch_or_pr.startswith(config.url)
            or not self.remote_name
        ):
            return config.owner
        elif URL_RE.match(self.branch_or_pr):
            return self.branch_or_pr.replace("https://github.com/", "").split("/", 1)[0]

        remote = self.runtime.get_remote(name=self.remote_name)
        if not remote:
            raise AssertionError("Couldn't find matching remote for --remote input")

        return remote.uri.replace("https://github.com/", "").split("/", 1)[0]

    @cached_property
    def remote(self) -> str:
        """The local name of the remote to use"""
        if self.remote_name:
            return self.remote_name
        remote = self.runtime.get_remote(owner_name=self.owner)
        if not remote:
            raise AssertionError("Couldn't find matching remote for PR")
        return remote.name

    @cached_property
    def pr_number(self) -> Optional[str]:
        """The PR number, if applicable"""
        if self.branch_or_pr.isdigit():
            return self.branch_or_pr

        if URL_RE.match(self.branch_or_pr):
            _, pr_number = self.branch_or_pr.rsplit("/", 1)
            return pr_number

        return None

    @cached_property
    def worktree_name(self) -> str:
        """The name of the worktree to create"""
        if self.pr_number:
            config = self.runtime.context.get_config()
            pr_status = self.runtime.gh.pr_status(
                self.pr_number, owner_repo=f"{self.owner}/{config.name}"
            )
            return pr_status["headRefName"]

        return self.branch_or_pr


class CheckoutCommand(Command):
    _name = "checkout"

    def __call__(self, branch_or_pr: str, remote: Optional[str] = None):  # noqa: C901
        """
        Checkout an existing branch or PR as a worktree
            gh-worktree checkout 1234
            gh-worktree checkout https://github.com/octo/repo/pull/1234
            gh-worktree checkout my-local-branch
            gh-worktree checkout a-branch --remote upstream

        :param branch_or_pr: The branch, PR number, or PR URL to create as a worktree
        :param remote: If `branch_or_pr` is a branch, this may be set to choose the remote to use
        """
        self._context.assert_within_project()

        inpt = CheckoutInput(self._runtime, str(branch_or_pr), remote_name=remote)
        inpt.validate()

        if inpt.pr_number:
            self._runtime.git.fetch(
                inpt.remote, f"pull/{inpt.pr_number}/head:{inpt.worktree_name}"
            )
        else:
            # TODO: detect if it's local only
            try:
                self._runtime.git.fetch(
                    inpt.remote, f"{inpt.worktree_name}:{inpt.worktree_name}"
                )
            except RuntimeError:
                print("Ignoring git fetch error, attempting to open worktree")
                pass

        with self._context.use(self._context.project_dir):
            self._runtime.hooks.fire(
                Hook.pre_checkout,
                inpt.worktree_name,
                f"{inpt.remote}/{inpt.worktree_name}",
            )
            self._runtime.git.open_worktree(inpt.worktree_name)
            self._runtime.hooks.fire(
                Hook.post_checkout,
                inpt.worktree_name,
                f"{inpt.remote}/{inpt.worktree_name}",
            )

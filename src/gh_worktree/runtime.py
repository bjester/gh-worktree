from typing import Optional

from gh_worktree.context import Context
from gh_worktree.gh import GithubCLI
from gh_worktree.git import GitCLI
from gh_worktree.git import GitRemote
from gh_worktree.hooks import Hooks


class Runtime(object):
    __slots__ = ("context", "hooks", "git", "gh")

    def __init__(self):
        self.context = Context()
        self.hooks = Hooks(self.context)
        self.git = GitCLI(self.context)
        self.gh = GithubCLI(self.context)

    def get_default_remote(self) -> Optional[GitRemote]:
        return self.get_remote(owner_name=self.context.get_config().owner)

    def get_remote(
        self, name: Optional[str] = None, owner_name: Optional[str] = None
    ) -> Optional[GitRemote]:
        remote_ref = None
        if owner_name:
            config = self.context.get_config()
            # forks could be renamed, but we're not gonna worry about that for now
            remote_ref = f"{owner_name}/{config.name}"
        elif not name:
            raise ValueError("Must provide either owner_name or name")

        for remote in self.git.remote():
            if remote.type != "fetch":
                continue
            if (remote_ref and remote_ref in remote.uri) or (
                name and name == remote.name
            ):
                return remote

        return None

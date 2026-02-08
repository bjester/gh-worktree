from typing import Optional

from gh_worktree.context import Context
from gh_worktree.gh import GithubCLI
from gh_worktree.git import GitCLI, GitRemote
from gh_worktree.hooks import Hooks


class Runtime(object):
    __slots__ = ("context", "hooks", "git", "gh")

    def __init__(self):
        self.context = Context()
        self.hooks = Hooks(self.context)
        self.git = GitCLI(self.context)
        self.gh = GithubCLI(self.context)

    def get_remote(self) -> Optional[GitRemote]:
        config = self.context.get_config()
        remotes = self.git.remote()
        remote_ref = f"{config.owner}/{config.name}"

        for remote in remotes:
            if remote.type == "fetch" and remote_ref in remote.uri:
                return remote

        return None

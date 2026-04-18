from gh_worktree.context import Context
from gh_worktree.errors import RemoteUsageError
from gh_worktree.gh import GithubCLI
from gh_worktree.git import GitCLI, GitRemote
from gh_worktree.hooks import Hooks
from gh_worktree.templates import Templates


class Runtime:
    __slots__ = ("verbose", "context", "hooks", "git", "gh", "templates")

    def __init__(self, verbose: bool = False):
        """
        :param verbose: Whether to enable logging verbosity
        """
        self.verbose = verbose
        self.context = Context()
        self.hooks = Hooks(self.context)
        self.git = GitCLI(self.context)
        self.gh = GithubCLI(self.context)
        self.templates = Templates(self.context)

    def get_default_remote(self) -> GitRemote | None:
        return self.get_remote(owner_name=self.context.get_config().owner)

    def get_remote(
        self, name: str | None = None, owner_name: str | None = None
    ) -> GitRemote | None:
        remote_ref = None
        if owner_name:
            config = self.context.get_config()
            # forks could be renamed, but we're not gonna worry about that for now
            remote_ref = f"{owner_name}/{config.name}"
        elif not name:
            raise RemoteUsageError("Must provide either owner_name or name")

        for remote in self.git.remote():
            if remote.type != "fetch":
                continue
            if (remote_ref and remote_ref in remote.uri) or (name and name == remote.name):
                return remote

        return None

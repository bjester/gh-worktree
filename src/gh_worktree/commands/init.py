import os
import re
from typing import Optional
from urllib import parse

from gh_worktree.command import Command
from gh_worktree.config import RepositoryConfig
from gh_worktree.hooks import Hook

JUST_PATH_RE = re.compile(r"^[\w\-_]+/[\w\-_]+$")
GIT_EXT_RE = re.compile(r"\.git$")


def normalize(repo: str):
    if not repo.startswith("http") and not repo.startswith("git@"):
        if not JUST_PATH_RE.match(repo):
            raise ValueError("Invalid repository path format. Expected: {owner}/{repo}")
        repo = f"https://github.com/{repo}"

    if not repo.endswith(".git"):
        repo += ".git"

    return repo


class RepositoryTarget(object):
    def __init__(self, repo: str, destination_dir: Optional[str] = None):
        self.uri = normalize(repo)
        self._destination_dir = destination_dir

    def validate(self):
        path_parts = self.path.split("/")
        if len(path_parts) != 2:
            raise ValueError(f"Invalid repository path: {self.path}")

    @property
    def path(self):
        if self.uri.startswith("http"):
            return parse.urlparse(self.uri).path.lstrip("/")
        # must be ssh
        _, path = self.uri.split(":")
        return path.lstrip("/")

    @property
    def owner(self):
        return self.path.split("/")[0]

    @property
    def name(self):
        return re.sub(GIT_EXT_RE, "", self.path.split("/")[1])

    @property
    def destination_dir(self):
        if self._destination_dir is None:
            return self.name
        return self._destination_dir


class InitCommand(Command):
    """Initialize a project for use with gh-worktree"""

    _name = "init"

    def __call__(self, repo: str, *destination_dir: Optional[str]):
        """
        Initialize a project for using gh-worktree with it, by cloning the project and configuring
        it to be a bare git repo.

        This command creates a suitable structure for worktree directories within the project
        directory. It accepts various input formats, but it must be a GitHub repository, since this
        uses `gh` to gather additional information about the project.

        Examples:
            gh-worktree init https://github.com/bjester/gh-worktree.git
            gh-worktree init ssh@github.com:bjester/gh-worktree.git
            gh-worktree init bjester/gh-worktree
            gh-worktree init bjester/gh-worktree gh-worktree-second

        :param repo: The URI, or Github 'owner/repo', to clone
        :type repo: str
        :param destination_dir: The destination directory to clone the project into.
        :type destination_dir: str
        """
        destination_dir = destination_dir[0] if destination_dir else None
        repo_target = RepositoryTarget(repo, destination_dir=destination_dir)
        repo_target.validate()

        project_dir = os.path.join(self._context.cwd, repo_target.destination_dir)

        if os.path.exists(project_dir):
            # this would be problematic!
            raise AssertionError(f"Project directory {project_dir} already exists")

        os.makedirs(project_dir, exist_ok=True)

        with self._context.use(project_dir):
            self._runtime.hooks.fire(
                Hook.pre_init,
                repo_target.uri,
                repo_target.destination_dir,
                skip_project=True,
            )
            self._runtime.git.clone(repo_target.uri, ".bare")

            with open(os.path.join(project_dir, ".git"), "w") as f:
                f.write("gitdir: ./.bare")

            self._runtime.git.config(
                "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"
            )
            self._runtime.git.fetch()
            repo_data = self._runtime.gh.repo_status()
            config = RepositoryConfig()
            config.update(
                default_branch=repo_data["defaultBranchRef"]["name"],
                owner=repo_data["owner"]["login"],
                name=repo_data["name"],
                url=repo_data["url"],
                is_private=repo_data["isPrivate"],
            )

            os.makedirs(self._context.config_dir, exist_ok=True)
            with open(os.path.join(self._context.config_dir, "config.json"), "w") as f:
                config.save(f)

        self._runtime.hooks.fire(
            Hook.post_init,
            repo_target.uri,
            repo_target.destination_dir,
            skip_project=True,
        )

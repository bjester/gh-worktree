import re
from collections import namedtuple

from gh_worktree.context import Context
from gh_worktree.utils import iter_output, stream_exec

TYPE_RE = re.compile(r"\((.*)\)")

GitRemote = namedtuple("GitRemote", ["name", "uri", "type"])


class GitCLI:
    def __init__(self, context: Context):
        self.context = context

    def _stream_exec(self, *command: str):
        return_status = stream_exec(["git", *command], cwd=self.context.cwd)
        if return_status != 0:
            raise RuntimeError(
                f"Command failed, with exit status {return_status}: git {' '.join(command)}"
            )

    def _iter_output(self, *command: str):
        yield from iter_output(["git", *command], cwd=self.context.cwd)

    def clone(self, src: str, destination_dir: str):
        self._stream_exec("clone", "--bare", src, destination_dir)

    def config(self, config_option: str, config_value: str):
        self._stream_exec("config", config_option, config_value)

    def ls_tree(self, branch_name: str, file_path: str):
        yield from self._iter_output("ls-tree", "-r", branch_name, "--", file_path)

    def cat_file(self, branch_name: str, file_path: str):
        yield from self._iter_output("cat-file", "-p", f"{branch_name}:{file_path}")

    def fetch(self, remote: str | None = "origin", refspec: str | None = None):
        if refspec is not None:
            self._stream_exec("fetch", remote, refspec)
        else:
            self._stream_exec("fetch", remote)

    def remote(self) -> list[GitRemote]:
        remotes = []
        for line in self._iter_output("remote", "-v"):
            name, uri_ref = line.split("\t")
            uri, remote_type = uri_ref.split(" ", 1)
            remotes.append(GitRemote(name, uri, re.sub(TYPE_RE, r"\1", remote_type)))
        return remotes

    def add_worktree(self, name: str, base_ref: str):
        """Create a new worktree branch off base_ref"""
        # Use -- to separate flags from positional arguments to prevent argument injection
        self._stream_exec("worktree", "add", "-b", name, "--", name, base_ref)

    def open_worktree(self, name: str):
        """Create a new worktree from an existing branch"""
        if ".." in name or name.startswith("/"):
            raise ValueError("Worktree name cannot contain '..' or start with '/'")
        # `git worktree add <path>` creates a new branch from HEAD. To use an
        # existing branch, the command is `git worktree add <path> <branch>`.
        # We pass `name` for both to check out the existing branch in a path with the same name.
        self._stream_exec("worktree", "add", "--", name, name)

    def remove_worktree(self, name: str, force: bool = False):
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append("--")
        args.append(name)
        self._stream_exec(*args)

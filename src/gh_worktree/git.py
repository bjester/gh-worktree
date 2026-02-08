import re
from collections import namedtuple
import subprocess
from typing import Union, Optional, List, Tuple

from gh_worktree.context import Context
from gh_worktree.utils import stream_exec

TYPE_RE = re.compile(r"\((.*)\)")

GitRemote = namedtuple("GitRemote", ["name", "uri", "type"])


class GitCLI(object):
    def __init__(self, context: Context):
        self.context = context

    def _stream_exec(self, *command: str):
        return_status = stream_exec(["git", *command], cwd=self.context.cwd)
        if return_status != 0:
            raise RuntimeError(
                f"Command failed, with exit status {return_status}: git {' '.join(command)}"
            )

    def clone(self, src: str, destination_dir: str):
        self._stream_exec("clone", "--bare", src, destination_dir)

    def config(self, config_option: str, config_value: str):
        self._stream_exec("config", config_option, config_value)

    def fetch(self, remote: Optional[str] = "origin", refspec: Optional[str] = None):
        if refspec is not None:
            self._stream_exec("fetch", remote, refspec)
        else:
            self._stream_exec("fetch", remote)

    def remote(self) -> List[GitRemote]:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            check=True,
            cwd=self.context.cwd,
        )
        remotes = []
        for line in result.stdout.splitlines():
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
        self._stream_exec("worktree", "add", "--", name)

    def remove_worktree(self, name: str, force: bool = False):
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append("--")
        args.append(name)
        self._stream_exec(*args)

import re
from collections import namedtuple
from collections.abc import Iterator
from pathlib import Path

from treefort.errors import CommandError, WorktreeNameError
from treefort.subprocess import SubprocessOperator

TYPE_RE = re.compile(r"\((.*)\)")

GitRemote = namedtuple("GitRemote", ["name", "uri", "type"])


class GitCLI(SubprocessOperator):
    command_name = "git"

    def stream_exec(self, command: list[str], cwd: str | Path | None = None) -> int:
        return_status = super().stream_exec(command, cwd=cwd)
        if return_status != 0:
            raise CommandError(
                f"Command failed, with exit status {return_status}: "
                f"{self.command_name} {' '.join(command)}"
            )
        return return_status

    def clone(self, src: str, destination_dir: str):
        self.stream_exec(["clone", "--bare", src, destination_dir])

    def config(self, config_option: str, config_value: str):
        self.stream_exec(["config", config_option, config_value])

    def ls_tree(self, branch_name: str, file_path: str) -> Iterator[str]:
        yield from self.iter_output(["ls-tree", "-r", branch_name, "--", file_path])

    def cat_file(self, branch_name: str, file_path: str) -> Iterator[str]:
        yield from self.iter_output(["cat-file", "-p", f"{branch_name}:{file_path}"])

    def fetch(self, remote: str = "origin", refspec: str | None = None):
        args = ["fetch", remote]
        if refspec is not None:
            args.append(refspec)
        self.stream_exec(args)

    def remote(self) -> list[GitRemote]:
        remotes = []
        for line in self.iter_output(["remote", "-v"]):
            name, uri_ref = line.split("\t")
            uri, remote_type = uri_ref.split(" ", 1)
            remotes.append(GitRemote(name, uri, re.sub(TYPE_RE, r"\1", remote_type)))
        return remotes

    def add_worktree(self, name: str, base_ref: str):
        """Create a new worktree branch off base_ref"""
        # Use -- to separate flags from positional arguments to prevent argument injection
        self.stream_exec(["worktree", "add", "-b", name, "--", name, base_ref])

    def open_worktree(self, name: str):
        """Create a new worktree from an existing branch"""
        if ".." in name or name.startswith("/"):
            raise WorktreeNameError("Worktree name cannot contain '..' or start with '/'")
        # `git worktree add <path>` creates a new branch from HEAD. To use an
        # existing branch, the command is `git worktree add <path> <branch>`.
        # We pass `name` for both to check out the existing branch in a path with the same name.
        self.stream_exec(["worktree", "add", "--", name, name])

    def remove_worktree(self, name: str, force: bool = False):
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.extend(["--", name])
        self.stream_exec(args)

    def list_worktrees(self) -> list[dict]:
        """List all worktrees and their associated branches"""
        worktrees = []
        current_worktree = None
        for line in self.iter_output(["worktree", "list", "--porcelain"]):
            if line.startswith("worktree "):
                current_worktree = {"path": line[9:], "branch": None, "is_bare": False}
                worktrees.append(current_worktree)
            elif line.startswith("branch ") and current_worktree:
                current_worktree["branch"] = line[7:]
            elif line == "bare" and current_worktree:
                current_worktree["is_bare"] = True
        return worktrees

    def delete_branch(self, name: str, force: bool = False):
        """Delete a local branch"""
        args = ["branch", "-d" if not force else "-D", "--", name]
        self.stream_exec(args)

    def get_branch_head(self, branch_name: str) -> str:
        """Get the HEAD commit SHA of a given branch"""
        with self.run(["rev-parse", branch_name]) as p:
            return p.stdout.strip()

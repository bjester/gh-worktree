from gh_worktree import __version__
from gh_worktree.runtime import Runtime
from gh_worktree.command import Command
from gh_worktree.commands.checkout import CheckoutCommand
from gh_worktree.commands.create import CreateCommand
from gh_worktree.commands.init import InitCommand
from gh_worktree.commands.remove import RemoveCommand


class WorktreeCommands(Command):
    """Github CLI extension for worktrees

    Can be used standalone but still requires the Github CLI (`gh`) to be installed.
    """

    def __init__(self):
        runtime = Runtime()
        super().__init__(runtime)
        self._add("create", CreateCommand(self._runtime))
        self._add("checkout", CheckoutCommand(self._runtime))
        self._add("init", InitCommand(self._runtime))
        self._add("remove", RemoveCommand(self._runtime))

    def _add(self, name: str, command: Command):
        """
        Get around where Fire wants keyword flags if commands are set as callable attributes. This
        approach allows positional arguments

        :param name: The attribute to assign the command's callable
        :param command: The command instance
        """
        setattr(self, f"_{name}", command)
        setattr(self, name, command.__call__)

    def version(self):
        """Outputs the version of gh-worktree"""
        print(f"gh-worktree {__version__}")


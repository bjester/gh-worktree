from gh_worktree import __version__
from gh_worktree.command import Command
from gh_worktree.commands.checkout import CheckoutCommand
from gh_worktree.commands.create import CreateCommand
from gh_worktree.commands.init import InitCommand
from gh_worktree.commands.install import InstallCommand
from gh_worktree.commands.remove import RemoveCommand
from gh_worktree.runtime import Runtime


class WorktreeCommands(Command):
    """Github CLI extension for worktrees

    Can be used standalone but still requires the Github CLI (`gh`) to be installed.
    """

    _name = "gh-worktree"

    def __init__(self):
        runtime = Runtime()
        super().__init__(runtime)
        self._add(CreateCommand(self._runtime))
        self._add(CheckoutCommand(self._runtime))
        self._add(InitCommand(self._runtime))
        self._add(InstallCommand(self._runtime))
        self._add(RemoveCommand(self._runtime))

    def _add(self, command: Command):
        """
        Get around where Fire wants keyword flags if commands are set as callable attributes. This
        approach allows positional arguments

        :param command: The command instance
        """
        setattr(self, command._name, command)
        setattr(self, command._name, command.__call__)
        for alias in command._aliases:
            setattr(self, alias, command.__call__)

    def version(self):
        """Outputs the version of gh-worktree"""
        print(f"gh-worktree {__version__}")

from functools import cached_property

from gh_worktree import __version__
from gh_worktree.command import Command
from gh_worktree.commands.checkout import CheckoutCommand
from gh_worktree.commands.create import CreateCommand
from gh_worktree.commands.init import InitCommand
from gh_worktree.commands.install import InstallCommand
from gh_worktree.commands.remove import RemoveCommand
from gh_worktree.errors import AliasConflictError
from gh_worktree.runtime import Runtime


class WorktreeCommands(Command):
    """Github CLI extension for worktrees

    Can be used standalone but still requires the Github CLI (`gh`) to be installed.
    """

    _name = "gh-worktree"

    def __init__(self, verbose: bool = False):
        """
        :param verbose: Whether to enable logging verbosity
        """
        runtime = Runtime(verbose)
        super().__init__(runtime)
        self._commands: list[Command] = []
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
        self._commands.append(command)
        setattr(self, command._name, command.__call__)

    @cached_property
    def _alias_map(self) -> dict[str, str]:
        alias_map = {}
        for command in self._commands:
            for alias in command._aliases:
                if alias in alias_map:
                    raise AliasConflictError(
                        f"Command {command._name} wants alias {alias} "
                        f"but it already exists for {alias_map[alias]}"
                    )
                alias_map[alias] = command._name
        return alias_map

    def version(self):
        """Outputs the version of the CLI"""
        print(f"{self._name} {__version__}")

    def aliases(self):
        """Outputs all of the command aliases"""
        for command in self._commands:
            if len(command._aliases) == 0:
                continue
            print(f"{command._name}: {', '.join(command._aliases)}")

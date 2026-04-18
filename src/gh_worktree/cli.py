import sys

import fire

from gh_worktree.main import WorktreeCommands


def replace_alias(cli: WorktreeCommands):
    """
    Replaces an alias with its corresponding full subcommand name in the system
    arguments if the provided subcommand is an alias.

    This function inspects the command-line arguments and, if an alias is found
    as the first subcommand, replaces it with the full subcommand name as defined
    in the alias map of the provided `WorktreeCommands` instance.

    :param cli: An instance of WorktreeCommands containing the alias map used to
                resolve aliases to their corresponding full subcommand names.
    """
    subcommand = sys.argv[1] if len(sys.argv) > 1 else None
    if subcommand is not None and subcommand in cli._alias_map.keys():
        sys.argv[1] = cli._alias_map[subcommand]


def main():
    """CLI tool for managing Git worktrees"""
    component = WorktreeCommands()
    replace_alias(component)
    # we do not pass `name` here, because the CLI allows using an alias for the command. if name
    # was passed, then using `worktree -- --completion` would use the wrong name for completion
    fire.Fire(component=component)

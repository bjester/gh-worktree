import fire
from gh_worktree.main import WorktreeCommands


def main():
    """CLI tool for managing Git worktrees"""
    commands = WorktreeCommands()
    fire.Fire(commands)

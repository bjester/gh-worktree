import fire

from gh_worktree.main import WorktreeCommands


def main():
    fire.Fire(WorktreeCommands, name="worktree")

import subprocess
from types import SimpleNamespace

from gh_worktree.git import GitCLI, GitRemote


def test_git_remote_parsing(monkeypatch):
    context = SimpleNamespace(cwd="/tmp")
    stdout = (
        "origin\tgit@github.com:foo/bar.git (fetch)\n"
        "origin\tgit@github.com:foo/bar.git (push)\n"
    )

    def fake_run(command, capture_output, text, check, cwd):
        assert command == ["git", "remote", "-v"]
        assert capture_output is True
        assert text is True
        assert check is True
        assert cwd == "/tmp"
        return SimpleNamespace(stdout=stdout)

    monkeypatch.setattr(subprocess, "run", fake_run)

    cli = GitCLI(context)
    remotes = cli.remote()

    assert remotes == [
        GitRemote("origin", "git@github.com:foo/bar.git", "fetch"),
        GitRemote("origin", "git@github.com:foo/bar.git", "push"),
    ]

from types import SimpleNamespace

from gh_worktree.git import GitRemote
from gh_worktree.runtime import Runtime


def test_get_remote_matches_fetch_remote(monkeypatch):
    runtime = Runtime()
    config = SimpleNamespace(owner="octo", name="repo")
    remotes = [
        GitRemote("origin", "git@github.com:octo/repo.git", "fetch"),
        GitRemote("origin", "git@github.com:octo/repo.git", "push"),
    ]

    monkeypatch.setattr(runtime.context, "get_config", lambda: config)
    monkeypatch.setattr(runtime.git, "remote", lambda: remotes)

    assert runtime.get_remote() == remotes[0]


def test_get_remote_returns_none_when_missing(monkeypatch):
    runtime = Runtime()
    config = SimpleNamespace(owner="octo", name="repo")
    remotes = [
        GitRemote("origin", "git@github.com:other/repo.git", "fetch"),
    ]

    monkeypatch.setattr(runtime.context, "get_config", lambda: config)
    monkeypatch.setattr(runtime.git, "remote", lambda: remotes)

    assert runtime.get_remote() is None

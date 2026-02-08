import json
import subprocess
from types import SimpleNamespace

from gh_worktree.gh import GithubCLI


def test_pr_status_calls_gh_and_parses_json(monkeypatch):
    context = SimpleNamespace(cwd="/repo")
    payload = {"number": 123, "title": "Example"}

    def fake_run(command, capture_output, text, check, cwd):
        assert command[:4] == ["gh", "pr", "view", "--json"]
        assert command[-1] == "123"
        assert capture_output is True
        assert text is True
        assert check is True
        assert cwd == "/repo"
        return SimpleNamespace(stdout=json.dumps(payload))

    monkeypatch.setattr(subprocess, "run", fake_run)

    cli = GithubCLI(context)
    result = cli.pr_status("123")

    assert result == payload


def test_repo_status_calls_gh_and_parses_json(monkeypatch):
    context = SimpleNamespace(cwd="/repo")
    payload = {"name": "repo", "owner": "me"}

    def fake_run(command, capture_output, text, check, cwd):
        assert command[:4] == ["gh", "repo", "view", "--json"]
        assert capture_output is True
        assert text is True
        assert check is True
        assert cwd == "/repo"
        return SimpleNamespace(stdout=json.dumps(payload))

    monkeypatch.setattr(subprocess, "run", fake_run)

    cli = GithubCLI(context)
    result = cli.repo_status()

    assert result == payload

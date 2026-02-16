import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from unittest import TestCase

from gh_worktree.gh import GithubCLI


class GithubCLITestCase(TestCase):
    def setUp(self):
        self.context = SimpleNamespace(cwd=Path("/repo"))

    def test_pr_status__calls_gh_and_parses_json(self):
        payload = {"number": 123, "title": "Example"}

        def fake_run(command, capture_output, text, check, cwd):
            self.assertEqual(command[:4], ["gh", "pr", "view", "--json"])
            self.assertEqual(command[-1], "123")
            self.assertTrue(capture_output)
            self.assertTrue(text)
            self.assertTrue(check)
            self.assertEqual(cwd, Path("/repo"))
            return SimpleNamespace(stdout=json.dumps(payload))

        with mock.patch.object(subprocess, "run", side_effect=fake_run):
            cli = GithubCLI(self.context)
            result = cli.pr_status("123")

        self.assertEqual(result, payload)

    def test_repo_status__calls_gh_and_parses_json(self):
        payload = {"name": "repo", "owner": "me"}

        def fake_run(command, capture_output, text, check, cwd):
            self.assertEqual(command[:4], ["gh", "repo", "view", "--json"])
            self.assertTrue(capture_output)
            self.assertTrue(text)
            self.assertTrue(check)
            self.assertEqual(cwd, Path("/repo"))
            return SimpleNamespace(stdout=json.dumps(payload))

        with mock.patch.object(subprocess, "run", side_effect=fake_run):
            cli = GithubCLI(self.context)
            result = cli.repo_status()

        self.assertEqual(result, payload)

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock

from gh_worktree.gh import PR_FIELDS, REPO_FIELDS, GithubCLI
from gh_worktree.logger import setup_logger


class GithubCLITestCase(TestCase):
    def setUp(self):
        self.context = SimpleNamespace(cwd=Path("/repo"))
        self.logger = setup_logger("test")
        self.gh = GithubCLI(self.context, self.logger)

    @mock.patch("gh_worktree.gh.SubprocessOperator.run")
    def test_pr_status__calls_gh_and_parses_json(self, mock_run):
        payload = {"number": 123, "title": "Example"}
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout=json.dumps(payload))
        mock_run.return_value.__enter__.return_value = process

        result = self.gh.pr_status(123)
        self.assertEqual(result, payload)
        mock_run.assert_called_once_with(["pr", "view", "--json", ",".join(PR_FIELDS), "123"])

    @mock.patch("gh_worktree.gh.SubprocessOperator.run")
    def test_pr_status__with_owner_repo(self, mock_run):
        payload = {"number": 123, "title": "Example"}
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout=json.dumps(payload))
        mock_run.return_value.__enter__.return_value = process

        result = self.gh.pr_status(123, owner_repo="me/repo")
        self.assertEqual(result, payload)
        mock_run.assert_called_once_with(
            ["pr", "view", "--repo", "me/repo", "--json", ",".join(PR_FIELDS), "123"]
        )

    @mock.patch("gh_worktree.gh.SubprocessOperator.run")
    def test_repo_status__calls_gh_and_parses_json(self, mock_run):
        payload = {"name": "repo", "owner": "me"}
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout=json.dumps(payload))
        mock_run.return_value.__enter__.return_value = process

        result = self.gh.repo_status()
        self.assertEqual(result, payload)
        mock_run.assert_called_once_with(["repo", "view", "--json", ",".join(REPO_FIELDS)])

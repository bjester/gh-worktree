import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock

from treefort.errors import CommandError
from treefort.gh import PR_FIELDS, REPO_FIELDS, GithubCLI
from treefort.logger import setup_logger


class GithubCLITestCase(TestCase):
    def setUp(self):
        self.context = SimpleNamespace(cwd=Path("/repo"))
        self.logger = setup_logger("test")
        self.gh = GithubCLI(self.context, self.logger)

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_pr_status__calls_gh_and_parses_json(self, mock_run):
        payload = {"number": 123, "title": "Example"}
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout=json.dumps(payload))
        mock_run.return_value.__enter__.return_value = process

        result = self.gh.pr_status(123)
        self.assertEqual(result, payload)
        mock_run.assert_called_once_with(["pr", "view", "--json", ",".join(PR_FIELDS), "123"])

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_pr_status__with_owner_repo(self, mock_run):
        payload = {"number": 123, "title": "Example"}
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout=json.dumps(payload))
        mock_run.return_value.__enter__.return_value = process

        result = self.gh.pr_status(123, owner_repo="me/repo")
        self.assertEqual(result, payload)
        mock_run.assert_called_once_with(
            ["pr", "view", "--repo", "me/repo", "--json", ",".join(PR_FIELDS), "123"]
        )

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_repo_status__calls_gh_and_parses_json(self, mock_run):
        payload = {"name": "repo", "owner": "me"}
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout=json.dumps(payload))
        mock_run.return_value.__enter__.return_value = process

        result = self.gh.repo_status()
        self.assertEqual(result, payload)
        mock_run.assert_called_once_with(["repo", "view", "--json", ",".join(REPO_FIELDS)])

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_merged_pr_by_head__calls_gh_and_parses_json(self, mock_run):
        payload = [{"number": 123, "headRefOid": "abc123"}]
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout=json.dumps(payload))
        mock_run.return_value.__enter__.return_value = process

        result = self.gh.merged_pr_by_head("feature-branch")
        self.assertEqual(result, payload)
        mock_run.assert_called_once_with(
            [
                "pr",
                "list",
                "--head",
                "feature-branch",
                "--state",
                "merged",
                "--json",
                ",".join(PR_FIELDS),
            ]
        )

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_merged_pr_by_head__returns_empty_list_for_successful_empty_response(self, mock_run):
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout="[]")
        mock_run.return_value.__enter__.return_value = process

        self.assertEqual(self.gh.merged_pr_by_head("feature-branch"), [])

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_merged_pr_by_head__with_owner_repo(self, mock_run):
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout="[]")
        mock_run.return_value.__enter__.return_value = process

        self.gh.merged_pr_by_head("feature-branch", owner_repo="octo/repo")
        mock_run.assert_called_once_with(
            [
                "pr",
                "list",
                "--head",
                "feature-branch",
                "--state",
                "merged",
                "--json",
                ",".join(PR_FIELDS),
                "--repo",
                "octo/repo",
            ]
        )

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_merged_pr_by_head__raises_command_error_when_gh_fails(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["gh", "pr", "list"], stderr="HTTP 401: Bad credentials"
        )

        with self.assertRaises(CommandError) as ctx:
            self.gh.merged_pr_by_head("feature-branch")

        message = str(ctx.exception)
        self.assertIn("feature-branch", message)
        self.assertIn("HTTP 401: Bad credentials", message)
        self.assertIsInstance(ctx.exception.__cause__, subprocess.CalledProcessError)

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_merged_pr_by_head__raises_command_error_when_output_is_malformed(self, mock_run):
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout="not json")
        mock_run.return_value.__enter__.return_value = process

        with self.assertRaises(CommandError) as ctx:
            self.gh.merged_pr_by_head("feature-branch")

        self.assertIn("feature-branch", str(ctx.exception))
        self.assertIsInstance(ctx.exception.__cause__, json.JSONDecodeError)

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_merged_pr_by_head__raises_command_error_when_response_is_not_a_list(self, mock_run):
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout="null")
        mock_run.return_value.__enter__.return_value = process

        with self.assertRaises(CommandError) as ctx:
            self.gh.merged_pr_by_head("feature-branch")

        self.assertIn("feature-branch", str(ctx.exception))
        self.assertIn("expected a list of PR objects", str(ctx.exception))

    @mock.patch("treefort.gh.SubprocessOperator.run")
    def test_merged_pr_by_head__raises_command_error_when_list_member_is_not_an_object(
        self, mock_run
    ):
        process = mock.MagicMock(spec=subprocess.CompletedProcess, stdout="[null]")
        mock_run.return_value.__enter__.return_value = process

        with self.assertRaises(CommandError) as ctx:
            self.gh.merged_pr_by_head("feature-branch")

        self.assertIn("feature-branch", str(ctx.exception))
        self.assertIn("expected a list of PR objects", str(ctx.exception))

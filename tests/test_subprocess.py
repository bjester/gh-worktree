import shlex
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase, mock
from unittest.mock import MagicMock, Mock

from gh_worktree.subprocess import SubprocessOperator, _log_prefix


class _SubprocessOperator(SubprocessOperator):
    """Test operator for SubprocessOperator class"""

    command_name = "test_command"


class SubprocessOperatorTestCase(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.context = Mock()
        self.context.cwd = self.tmp_path
        self.logger = Mock()
        self.operator = _SubprocessOperator(self.context, self.logger)

    def tearDown(self):
        self.tmp_dir.cleanup()

    @mock.patch("gh_worktree.subprocess.subprocess.Popen")
    def test_stream_exec(self, mock_popen):
        process_mock = MagicMock()
        process_mock.stdout = ["line1\n", "line2\n"]
        process_mock.returncode = 0
        process_mock.pid = 123
        process_mock.poll.side_effect = [None, None, 0]
        mock_popen.return_value = process_mock

        command = ["do-something"]
        exit_code = self.operator.stream_exec(command)

        expected_command = ["test_command", "do-something"]
        mock_popen.assert_called_once_with(
            expected_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=self.tmp_path,
        )

        self.assertEqual(exit_code, 0)
        self.logger.info.assert_any_call(
            f"Executing: {shlex.join(expected_command)}", extra=mock.ANY
        )
        self.assertEqual(self.logger.log.call_count, 2)

    @mock.patch("gh_worktree.subprocess.subprocess.Popen")
    def test_stream_exec__timeout_kills_process(self, mock_popen):
        process_mock = MagicMock()
        process_mock.stdout = []
        process_mock.pid = 123
        process_mock.poll.return_value = None
        mock_popen.return_value = process_mock
        self.operator.wait_time = 0

        with self.assertRaises(subprocess.TimeoutExpired):
            self.operator.stream_exec(["do-something"])

        process_mock.kill.assert_called_once_with()
        process_mock.wait.assert_called_once_with()

    @mock.patch("gh_worktree.subprocess.subprocess.run")
    def test_run(self, mock_run):
        result_mock = Mock(spec=subprocess.CompletedProcess, stdout="line1\nline2")
        mock_run.return_value = result_mock

        command = ["get-data"]
        output = self.operator.run(command)

        expected_command = ["test_command", "get-data"]
        mock_run.assert_called_once_with(
            expected_command,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
            cwd=self.tmp_path,
        )

        self.assertEqual(output, result_mock)

    @mock.patch("gh_worktree.subprocess.subprocess.run")
    def test_iter_output(self, mock_run):
        result_mock = Mock()
        result_mock.stdout = "line1\nline2"
        mock_run.return_value = result_mock

        command = ["get-data"]
        output = list(self.operator.iter_output(command))

        expected_command = ["test_command", "get-data"]
        mock_run.assert_called_once_with(
            expected_command,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
            cwd=self.tmp_path,
        )

        self.assertEqual(output, ["line1", "line2"])
        self.logger.info.assert_called_once()
        self.assertEqual(self.logger.log.call_count, 2)


class LogPrefixTestCase(TestCase):
    def test_basic(self):
        self.assertEqual(_log_prefix(["git", "status"]), "git status")

    def test_script_path(self):
        with tempfile.NamedTemporaryFile() as tmp:
            script_path = Path(tmp.name)
            self.assertEqual(_log_prefix([str(script_path), "run"]), f"{script_path.name} run")

    def test_arg_limit(self):
        self.assertEqual(_log_prefix(["git", "diff", "--", "path/to/file"]), "git diff")

import queue
import random
import shlex
import subprocess
import threading
import time
from collections.abc import Iterator
from contextlib import ContextDecorator
from pathlib import Path

from gh_worktree.logger import COMMAND_OUTPUT
from gh_worktree.operator import RuntimeOperator

# These are the allowed colors for command output, to avoid conflict with red/yellow errors/warnings
ALLOWED_COLORS = ["green", "blue", "magenta", "cyan"]


def _log_prefix(command: list[str]) -> str:
    """
    Returns a prefix string for visibility, via logging, into the command being executed
    :param command: The command list to be executed
    :return: A string for prefixing log messages
    """
    command_prefix = command[:2]
    command_script_path = Path(command_prefix[0])
    if command_script_path.exists():
        command_prefix[0] = command_script_path.name

    return shlex.join(command_prefix)


def _output_thread(process: subprocess.Popen) -> tuple[queue.Queue[str], threading.Thread]:
    """
    Creates a thread that queues the process output to be read by the main thread
    :param process: The process to read output from
    :return: A tuple of the output queue and reader thread
    """
    output_queue: queue.Queue[str] = queue.Queue()

    def enqueue_output() -> None:
        if process.stdout is None:
            return
        for line in process.stdout:
            output_queue.put(line)

    reader_thread = threading.Thread(target=enqueue_output, daemon=True)
    reader_thread.start()
    return output_queue, reader_thread


class RandomColorState(threading.local):
    depth: int = 0
    color: str | None = None


class RandomColorDecorator(ContextDecorator):
    """Maintains the same color across decorated calls within the same context"""

    def __init__(self):
        self._state = RandomColorState()

    @property
    def color(self) -> str | None:
        return self._state.color

    def __enter__(self):
        self._state.depth += 1
        if self._state.color is None:
            self._state.color = random.choice(ALLOWED_COLORS)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._state.depth -= 1
        if self._state.depth == 0:
            self._state.color = None


random_color = RandomColorDecorator()


class SubprocessOperator(RuntimeOperator):
    wait_time: int = 60
    """The number of seconds to wait for a process to finish"""
    command_name: str | None = None
    """The name of the command being executed, prepended to the command list"""

    def stream_exec(self, command: list[str], cwd: str | Path | None = None) -> int:
        """
        Executes a command in a subprocess and streams its output to stdout.
        :param command: The command to execute as a list of strings
        :param cwd: The working directory to execute the command in
        :return: The exit code of the process
        """
        if self.command_name:
            command = [self.command_name, *command]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd or self.context.cwd,
        )
        output_queue, reader_thread = _output_thread(process)
        deadline = time.monotonic() + self.wait_time

        try:
            color = ALLOWED_COLORS[process.pid % len(ALLOWED_COLORS)]
            self.logger.info(f"Executing: {shlex.join(command)}", extra={"color": color})

            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 and process.poll() is None:
                    raise subprocess.TimeoutExpired(command, self.wait_time)

                try:
                    line = output_queue.get(timeout=max(0.01, min(0.1, remaining)))
                except queue.Empty:
                    # Drain any buffered tail lines before exiting once process is done.
                    if (
                        process.poll() is not None
                        and not reader_thread.is_alive()
                        and output_queue.empty()
                    ):
                        break
                    continue

                self.logger.log(
                    COMMAND_OUTPUT,
                    f"{_log_prefix(command)} | {line.rstrip()}",
                    extra={"color": color},
                )

            process.wait()
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise
        finally:
            if process.stdout and hasattr(process.stdout, "close"):
                process.stdout.close()
            reader_thread.join(timeout=0.5)

        return process.returncode

    @random_color
    def run(self, command: list[str], cwd: str | Path | None = None) -> subprocess.CompletedProcess:
        """
        Executes a command in a subprocess and returns the completed process
        :param command: The command to execute as a list of strings
        :param cwd: The working directory to execute the command in
        """
        if self.command_name:
            command = [self.command_name, *command]

        self.logger.info(f"Executing: {shlex.join(command)}", extra={"color": random_color.color})

        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=self.wait_time,
            cwd=cwd or self.context.cwd,
        )

    @random_color
    def iter_output(self, command: list[str], cwd: str | Path | None = None) -> Iterator[str]:
        """
        Executes a command in a subprocess and iterates its output after completion
        :param command: The command to execute as a list of strings
        :param cwd: The working directory to execute the command in
        """
        for line in self.run(command, cwd=cwd).stdout.splitlines():
            self.logger.log(
                COMMAND_OUTPUT,
                f"{_log_prefix(command)} | {line}",
                extra={"color": random_color.color},
            )
            yield line

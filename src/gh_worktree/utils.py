import random
import shlex
import subprocess
from pathlib import Path
from typing import List
from typing import Optional
from typing import Union

# Simple ANSI colors for the prefix
COLORS = ["\033[92m", "\033[94m", "\033[95m", "\033[96m", "\033[93m"]
COLOR_RESET = "\033[0m"


def find_up(name: str, start_path: Union[str, Path]) -> Path:
    """
    Looks upward for a directory that has file or directory with `name`
    :param name: The name of the file or directory to look for
    :param start_path: The path to start looking from
    :return: The path to the directory
    """
    search_path = Path(start_path).resolve()

    while True:
        name_path = search_path / name
        if search_path.is_dir() and name_path.exists():
            return name_path
        if search_path == search_path.parent:
            break
        search_path = search_path.parent

    raise RuntimeError(f"Could not find {name} in {start_path} ancestors")


def _log_prefix(command: List[str]) -> str:
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


def stream_exec(
    command: List[str], wait_time: int = 60, cwd: Optional[Union[str, Path]] = None
) -> int:
    """
    Executes a command in a subprocess and streams its output to stdout.
    :param command: The command to execute as a list of strings
    :param wait_time: The number of seconds to wait for the process to finish
    :param cwd: The working directory to execute the command in
    :return: The exit code of the process
    """
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=cwd,
    ) as process:
        output_color = COLORS[process.pid % len(COLORS)]
        print(f"Executing: {output_color}{shlex.join(command)}{COLOR_RESET}")

        for line in process.stdout:
            print(
                f"{output_color}{_log_prefix(command)} |{COLOR_RESET} {line}",
                end="",
                flush=True,
            )

        process.wait(wait_time)

    return process.returncode


def iter_output(
    command: List[str], wait_time: int = 60, cwd: Optional[Union[str, Path]] = None
):
    """
    Executes a command in a subprocess and iterates its output after completion
    :param command: The command to execute as a list of strings
    :param wait_time: The number of seconds to wait for the process to finish
    :param cwd: The working directory to execute the command in
    """
    output_color = random.choice(COLORS)
    print(f"Executing: {output_color}{shlex.join(command)}{COLOR_RESET}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        timeout=wait_time,
        cwd=cwd,
    )

    for line in result.stdout.splitlines():
        print(
            f"{output_color}{_log_prefix(command)} |{COLOR_RESET} {line}",
            flush=True,
        )
        yield line

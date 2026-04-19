"""Logging utility for gh-worktree CLI."""

import logging
import sys
from pathlib import Path

# ANSI color codes
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "reset": "\033[0m",
}

# Custom log level for command output
COMMAND_OUTPUT = logging.DEBUG - 1
logging.addLevelName(COMMAND_OUTPUT, "COMMAND_OUTPUT")


class ColorFormatter(logging.Formatter):
    """Formatter that applies colors based on log level or explicit color."""

    LEVEL_COLORS = {
        logging.DEBUG: COLORS["cyan"],
        COMMAND_OUTPUT: COLORS["blue"],
        logging.INFO: COLORS["green"],
        logging.WARNING: COLORS["yellow"],
        logging.ERROR: COLORS["red"],
        logging.CRITICAL: COLORS["magenta"],
    }

    def __init__(self, fmt: str, use_color: bool = True):
        super().__init__(fmt)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        # Use explicit color from extra if provided, otherwise use level-based color
        color = getattr(record, "color", None)
        if color and color in COLORS:
            color_code = COLORS[color]
        else:
            color_code = self.LEVEL_COLORS.get(record.levelno, COLORS["reset"])

        message = super().format(record)
        if self.use_color and color_code:
            return f"{color_code}{message}{COLORS['reset']}"
        return message


def setup_logger(
    name: str = "gh-worktree",
    log_dir: Path | None = None,
    verbose: bool = False,
    debug_log_path: Path | None = None,
) -> logging.Logger:
    """
    Set up logging with console and file handlers.

    :param name: Logger name
    :param log_dir: Directory for log files (defaults to ~/.gh/worktree/logs)
    :param verbose: Enable debug logging with full subprocess output
    :param debug_log_path: Specific path for debug log file
    :return: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers = []  # Clear existing handlers

    # Console formatter - colored, no timestamp for user-facing output
    console_fmt = "%(message)s"
    console_formatter = ColorFormatter(console_fmt, use_color=sys.stdout.isatty())

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handlers (if log_dir provided)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)

        # Default log file - timestamps and commands
        default_log_file = log_dir / "gh-worktree.log"
        file_fmt = "%(asctime)s - %(levelname)s - %(message)s"
        file_formatter = logging.Formatter(file_fmt, datefmt="%Y-%m-%d %H:%M:%S")

        file_handler = logging.FileHandler(default_log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Debug log file (if verbose or debug_log_path specified)
        if verbose or debug_log_path:
            debug_file = debug_log_path or (log_dir / "gh-worktree-debug.log")
            debug_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            debug_handler = logging.FileHandler(debug_file, encoding="utf-8")
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(debug_formatter)
            logger.addHandler(debug_handler)

            # Also log command output to debug file
            console_handler.setLevel(logging.DEBUG)

    return logger


def get_logger(name: str = "gh-worktree") -> logging.Logger:
    """Get an existing logger by name."""
    return logging.getLogger(name)


def log_command(
    logger: logging.Logger,
    command: list[str],
    color: str | None = None,
    output: str | None = None,
):
    """
    Log a command being executed with optional color and output.

    :param logger: Logger instance
    :param command: Command list to log
    :param color: Color to use for the command output
    :param output: Optional command output to log at COMMAND_OUTPUT level
    """
    import shlex

    color = color or "blue"
    logger.info(f"Executing: {shlex.join(command)}", extra={"color": color})

    if output:
        for line in output.splitlines():
            logger.log(COMMAND_OUTPUT, line, extra={"color": color})

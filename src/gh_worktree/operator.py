import logging
from collections.abc import Iterator
from pathlib import Path

from gh_worktree.context import Context


class RuntimeOperator:
    """
    Base class for utility classes that are attached to the Runtime object.
    """

    def __init__(self, context: Context, logger: logging.Logger):
        self.context = context
        self.logger = logger


class ConfigOperator(RuntimeOperator):
    """
    Base class for utility classes that rely on the configuration directories.
    """

    dir_name: str

    def iter_config_dirs(self, skip_project: bool = False) -> Iterator[Path]:
        configs = [self.context.global_config_dir]
        if not skip_project:
            configs.append(self.context.config_dir)

        for config_dir in configs:
            op_dir = config_dir / self.dir_name
            if not op_dir.exists():
                continue

            yield op_dir

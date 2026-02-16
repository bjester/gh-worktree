from pathlib import Path
from typing import Iterator

from gh_worktree.context import Context


class ConfigOperator(object):
    dir_name: str

    def __init__(self, context: Context):
        self.context = context

    def iter_config_dirs(self, skip_project: bool = False) -> Iterator[Path]:
        configs = [self.context.global_config_dir]
        if not skip_project:
            configs.append(self.context.config_dir)

        for config_dir in configs:
            op_dir = config_dir / self.dir_name
            if not op_dir.exists():
                continue

            yield op_dir

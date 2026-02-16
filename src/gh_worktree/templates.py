import os
from pathlib import Path
from string import Template

from gh_worktree.context import Context
from gh_worktree.operator import ConfigOperator


class Templates(ConfigOperator):
    """
    Copies files from /templates directory into a worktree, replacing environment variables in the
    process.
    """

    def __init__(self, context: Context):
        super().__init__(context)
        self.dir_name = "templates"
        self.replacement_map = {}

        global_config = context.get_global_config()
        for envvar_name in global_config.allowed_envvars:
            self.replacement_map[envvar_name] = os.environ.get(envvar_name, "")

    def copy(self, worktree_name: str):
        config = self.context.get_config()
        worktree_dir = Path(os.path.join(self.context.project_dir, worktree_name))

        self.replacement_map["REPO_NAME"] = config.name
        self.replacement_map["REPO_DIR"] = self.context.project_dir
        self.replacement_map["WORKTREE_NAME"] = worktree_name
        self.replacement_map["WORKTREE_DIR"] = str(worktree_dir)

        for templates_dir in self.iter_config_dirs():
            for path in Path(templates_dir).rglob("*"):
                relative_path = path.relative_to(templates_dir)
                self._copy(worktree_dir, path, relative_path)

    def _copy(self, worktree_dir: Path, absolute_path: Path, relative_path: Path):
        dest_path = worktree_dir / relative_path

        if absolute_path.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
            return

        print(f"Copying template {relative_path}")
        with absolute_path.open("r", encoding="utf-8") as src:
            with dest_path.open("w", encoding="utf-8") as dest:
                content = src.read()
                dest.write(Template(content).safe_substitute(self.replacement_map))

        dest_path.chmod(absolute_path.stat().st_mode)

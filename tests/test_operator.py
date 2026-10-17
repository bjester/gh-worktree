from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase

from treefort.gh import GithubCLI
from treefort.git import GitCLI
from treefort.logger import setup_logger
from treefort.templates import Templates


class RuntimeOperatorLoggerTestCase(TestCase):
    def setUp(self):
        self.context = SimpleNamespace(
            cwd=Path("/repo"),
            get_global_config=lambda: SimpleNamespace(allowed_envvars=[]),
        )
        self.logger = setup_logger("test")

    def test_gh_operator_uses_module_child_logger(self):
        cli = GithubCLI(self.context, self.logger)
        self.assertEqual(cli.logger.name, "test.gh")

    def test_git_operator_uses_module_child_logger(self):
        cli = GitCLI(self.context, self.logger)
        self.assertEqual(cli.logger.name, "test.git")

    def test_templates_operator_uses_module_child_logger(self):
        templates = Templates(self.context, self.logger)
        self.assertEqual(templates.logger.name, "test.templates")

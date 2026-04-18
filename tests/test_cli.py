from unittest import TestCase
from unittest.mock import Mock, patch

import gh_worktree.cli as cli_module
from gh_worktree.cli import main, replace_alias


class ReplaceAliasTestCase(TestCase):
    @patch("gh_worktree.cli.sys.argv", ["gh-worktree", "rm", "feature-branch"])
    def test_rewrites_first_arg_when_alias_exists(self):
        cli = Mock()
        cli._alias_map = {"rm": "remove"}

        replace_alias(cli)

        self.assertEqual("remove", cli._alias_map["rm"])
        self.assertEqual("remove", cli_module.sys.argv[1])

    @patch("gh_worktree.cli.sys.argv", ["gh-worktree", "remove", "feature-branch"])
    def test_noop_when_arg_is_not_alias(self):
        cli = Mock()
        cli._alias_map = {"rm": "remove"}

        replace_alias(cli)

        self.assertEqual("remove", cli_module.sys.argv[1])

    @patch("gh_worktree.cli.sys.argv", ["gh-worktree"])
    def test_noop_when_no_subcommand(self):
        cli = Mock()
        cli._alias_map = {"rm": "remove"}

        replace_alias(cli)

        self.assertEqual(["gh-worktree"], cli_module.sys.argv)


class MainTestCase(TestCase):
    @patch("gh_worktree.cli.fire.Fire")
    @patch("gh_worktree.cli.replace_alias")
    @patch("gh_worktree.cli.WorktreeCommands")
    def test_main__builds_component_replaces_aliases_and_invokes_fire(
        self,
        commands_cls_mock,
        replace_alias_mock,
        fire_mock,
    ):
        component = Mock()
        commands_cls_mock.return_value = component

        main()

        commands_cls_mock.assert_called_once_with()
        replace_alias_mock.assert_called_once_with(component)
        fire_mock.assert_called_once_with(component=component)

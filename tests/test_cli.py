from unittest import TestCase
from unittest.mock import Mock, patch

import gh_worktree.cli as cli_module
from gh_worktree.cli import main, replace_alias, replace_verbose


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
    @patch("gh_worktree.cli.replace_verbose")
    @patch("gh_worktree.cli.WorktreeCommands")
    def test_main__builds_component_replaces_aliases_and_invokes_fire(
        self,
        commands_cls_mock,
        replace_verbose_mock,
        replace_alias_mock,
        fire_mock,
    ):
        component = Mock()
        commands_cls_mock.return_value = component
        replace_verbose_mock.return_value = False

        main()

        replace_verbose_mock.assert_called_once_with()
        commands_cls_mock.assert_called_once_with(verbose=False)
        replace_alias_mock.assert_called_once_with(component)
        fire_mock.assert_called_once_with(component=component)


class ReplaceVerboseTestCase(TestCase):
    @patch("gh_worktree.cli.sys.argv", ["gh-worktree", "-v", "remove", "feature"])
    def test_rewrites_args_and_returns_true_for_short_flag(self):
        is_verbose = replace_verbose()

        self.assertTrue(is_verbose)
        self.assertEqual(["gh-worktree", "remove", "feature"], cli_module.sys.argv)

    @patch(
        "gh_worktree.cli.sys.argv",
        ["gh-worktree", "--verbose", "remove", "feature"],
    )
    def test_rewrites_args_and_returns_true_for_long_flag(self):
        is_verbose = replace_verbose()

        self.assertTrue(is_verbose)
        self.assertEqual(["gh-worktree", "remove", "feature"], cli_module.sys.argv)

    @patch(
        "gh_worktree.cli.sys.argv",
        ["gh-worktree", "-v", "--verbose", "remove", "feature"],
    )
    def test_consumes_all_verbose_flags_before_passthrough_separator(self):
        is_verbose = replace_verbose()

        self.assertTrue(is_verbose)
        self.assertEqual(["gh-worktree", "remove", "feature"], cli_module.sys.argv)

    @patch(
        "gh_worktree.cli.sys.argv",
        ["gh-worktree", "remove", "--", "--verbose", "-v", "feature"],
    )
    def test_does_not_strip_verbose_flags_after_passthrough_separator(self):
        is_verbose = replace_verbose()

        self.assertFalse(is_verbose)
        self.assertEqual(
            ["gh-worktree", "remove", "--", "--verbose", "-v", "feature"],
            cli_module.sys.argv,
        )

    @patch("gh_worktree.cli.sys.argv", ["gh-worktree", "remove", "feature"])
    def test_noop_when_no_verbose_flag_is_present(self):
        is_verbose = replace_verbose()

        self.assertFalse(is_verbose)
        self.assertEqual(["gh-worktree", "remove", "feature"], cli_module.sys.argv)

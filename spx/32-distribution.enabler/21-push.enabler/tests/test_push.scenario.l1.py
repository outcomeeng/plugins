"""Level-1 scenario evidence for `spx/32-distribution.enabler/21-push.enabler/`."""

from __future__ import annotations

from outcomeeng_testing.harnesses.push import (
    cli_parser_forwards_git_help_flag_verbatim,
    cli_parser_forwards_leading_git_options_verbatim,
    clustered_short_option_dry_run_does_not_refresh_marketplace,
    dry_run_push_does_not_refresh_marketplace,
    failed_git_push_propagates_exit_code_and_skips_sync,
    git_help_push_does_not_refresh_marketplace,
    long_git_help_push_does_not_refresh_marketplace,
    no_dry_run_option_restores_marketplace_refresh,
    no_push_args_forwards_bare_git_push,
    push_option_operand_named_like_dry_run_still_refreshes_marketplace,
    repo_option_operand_named_like_dry_run_still_refreshes_marketplace,
    separator_repository_named_like_dry_run_still_refreshes_marketplace,
    tracked_branch_captures_upstream_and_invokes_sync_with_ref,
    untracked_branch_invokes_sync_without_ref,
)


def test_tracked_branch_captures_upstream_and_invokes_sync_with_ref() -> None:
    assert tracked_branch_captures_upstream_and_invokes_sync_with_ref()


def test_untracked_branch_invokes_sync_without_ref() -> None:
    assert untracked_branch_invokes_sync_without_ref()


def test_failed_git_push_propagates_exit_code_and_skips_sync() -> None:
    assert failed_git_push_propagates_exit_code_and_skips_sync()


def test_no_push_args_forwards_bare_git_push() -> None:
    assert no_push_args_forwards_bare_git_push()


def test_cli_parser_forwards_leading_git_options_verbatim() -> None:
    assert cli_parser_forwards_leading_git_options_verbatim()


def test_cli_parser_forwards_git_help_flag_verbatim() -> None:
    assert cli_parser_forwards_git_help_flag_verbatim()


def test_git_help_push_does_not_refresh_marketplace() -> None:
    assert git_help_push_does_not_refresh_marketplace()


def test_long_git_help_push_does_not_refresh_marketplace() -> None:
    assert long_git_help_push_does_not_refresh_marketplace()


def test_dry_run_push_does_not_refresh_marketplace() -> None:
    assert dry_run_push_does_not_refresh_marketplace()


def test_clustered_short_option_dry_run_does_not_refresh_marketplace() -> None:
    assert clustered_short_option_dry_run_does_not_refresh_marketplace()


def test_no_dry_run_option_restores_marketplace_refresh() -> None:
    assert no_dry_run_option_restores_marketplace_refresh()


def test_push_option_operand_named_like_dry_run_still_refreshes_marketplace() -> None:
    assert push_option_operand_named_like_dry_run_still_refreshes_marketplace()


def test_repo_option_operand_named_like_dry_run_still_refreshes_marketplace() -> None:
    assert repo_option_operand_named_like_dry_run_still_refreshes_marketplace()


def test_separator_repository_named_like_dry_run_still_refreshes_marketplace() -> None:
    assert separator_repository_named_like_dry_run_still_refreshes_marketplace()

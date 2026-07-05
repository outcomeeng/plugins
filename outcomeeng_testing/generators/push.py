"""Generator-owned push argument vectors for push orchestration tests."""

from outcomeeng.distribution.push import (
    DRY_RUN_PUSH_FLAGS,
    HELP_PUSH_FLAGS,
    NO_DRY_RUN_PUSH_FLAG,
    PUSH_OPTION_FLAGS,
)


def tracked_upstream_ref() -> str:
    return "abc123"


def push_failure_exit_code() -> int:
    return 7


def sync_failure_exit_code() -> int:
    return 13


def force_with_lease_push_args() -> tuple[str, ...]:
    return ("--force-with-lease", "origin", "HEAD:refs/heads/feature")


def git_help_push_args() -> tuple[str, ...]:
    return ("-h",)


def clustered_git_help_push_args() -> tuple[str, ...]:
    return ("-vh",)


def long_git_help_push_args() -> tuple[str, ...]:
    return (next(iter(sorted(HELP_PUSH_FLAGS - {"-h"}))),)


def dry_run_push_args() -> tuple[str, ...]:
    return (next(iter(sorted(DRY_RUN_PUSH_FLAGS))), "origin", "HEAD:refs/heads/feature")


def clustered_dry_run_push_args() -> tuple[str, ...]:
    return ("-vn", "origin", "HEAD:refs/heads/feature")


def dry_run_then_no_dry_run_push_args() -> tuple[str, ...]:
    return ("--dry-run", NO_DRY_RUN_PUSH_FLAG, "origin", "HEAD:refs/heads/feature")


def push_option_with_dry_run_operand_args() -> tuple[str, ...]:
    return (
        next(iter(sorted(PUSH_OPTION_FLAGS))),
        "-n",
        "origin",
        "HEAD:refs/heads/feature",
    )


def repo_option_with_dry_run_operand_args() -> tuple[str, ...]:
    return ("--repo", "-n", "origin", "HEAD:refs/heads/feature")


def separator_repository_named_like_dry_run_args() -> tuple[str, ...]:
    return ("--", "-n", "HEAD:refs/heads/feature")


def recurse_submodules_bare_dry_run_args() -> tuple[str, ...]:
    return ("--recurse-submodules", "--dry-run", "origin", "HEAD:refs/heads/feature")


def recurse_submodules_bare_help_args() -> tuple[str, ...]:
    return ("--recurse-submodules", "--help")

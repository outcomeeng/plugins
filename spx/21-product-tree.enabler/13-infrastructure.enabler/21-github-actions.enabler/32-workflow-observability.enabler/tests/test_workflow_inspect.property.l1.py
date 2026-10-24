"""Property evidence: `workflow_inspect.py` input validation, failure reporting, and log truncation."""

from __future__ import annotations

import json

from hypothesis import strategies as st

from outcomeeng_testing.generators.workflow_inspect import (
    LogCase,
    failing_exit_codes,
    id_subcommands,
    invalid_numbers,
    log_cases,
    non_positive_integers,
    stderr_texts,
    valid_numbers,
)
from outcomeeng_testing.harnesses.workflow_inspect import (
    GhReply,
    run_cli,
    workflow_inspect_property,
)

RUN_ID_SOURCE = "`workflow_inspect.py runs`"
PR_NUMBER_SOURCE = "`gh pr list` or the PR URL"


@workflow_inspect_property(
    st.tuples(id_subcommands(), invalid_numbers()), argument="case"
)
def _invalid_numbers_are_rejected_before_any_gh_call(case: tuple[str, str]) -> None:
    subcommand, value = case

    observed = run_cli([subcommand, value], GhReply(0, "{}"))

    label = "pull request number" if subcommand == "checks" else "run id"
    source = PR_NUMBER_SOURCE if subcommand == "checks" else RUN_ID_SOURCE
    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert observed.gh_calls == ()
    assert payload["error"] == (
        f"{subcommand} {value}: {label} must be a positive integer, got '{value}'. "
        f"Next: pass the number from {source}."
    )


def test_invalid_run_ids_and_pr_numbers_are_rejected_before_any_gh_call() -> None:
    _invalid_numbers_are_rejected_before_any_gh_call()


@workflow_inspect_property(
    st.tuples(id_subcommands(), valid_numbers()), argument="case"
)
def _valid_numbers_reach_gh_exactly_once(case: tuple[str, str]) -> None:
    subcommand, value = case

    observed = run_cli([subcommand, value], GhReply(0, "{}"))

    assert len(observed.gh_calls) == 1
    assert value in " ".join(observed.gh_calls[0])


def test_valid_run_ids_and_pr_numbers_reach_gh_exactly_once() -> None:
    _valid_numbers_reach_gh_exactly_once()


@workflow_inspect_property(non_positive_integers(), argument="limit")
def _limits_below_one_are_rejected(limit: int) -> None:
    observed = run_cli(["runs", f"--limit={limit}"], GhReply(0, "[]"))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert observed.gh_calls == ()
    assert payload["runs"] == []
    assert payload["error"] == (
        f"runs --limit {limit}: limit must be at least 1. "
        "Next: pass --limit with a positive integer."
    )


def test_runs_limit_below_one_is_rejected_before_any_gh_call() -> None:
    _limits_below_one_are_rejected()


@workflow_inspect_property(non_positive_integers(), argument="max_bytes")
def _max_bytes_below_one_are_rejected(max_bytes: int) -> None:
    observed = run_cli(["log", "9001", f"--max-bytes={max_bytes}"], GhReply(0, "log"))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert observed.gh_calls == ()
    assert payload["log"] == ""
    assert payload["error"] == (
        f"log --max-bytes {max_bytes}: max-bytes must be at least 1. "
        "Next: pass --max-bytes with a positive integer."
    )


def test_log_max_bytes_below_one_is_rejected_before_any_gh_call() -> None:
    _max_bytes_below_one_are_rejected()


@workflow_inspect_property(
    st.tuples(failing_exit_codes(), stderr_texts()), argument="case"
)
def _gh_failures_report_code_and_stderr(case: tuple[int, str]) -> None:
    code, stderr = case

    observed = run_cli(["workflow-files"], GhReply(code, "", stderr))

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 1
    assert payload["error"] == (
        f"workflow-files: gh workflow list exited {code}: {stderr}. "
        "Next: run python3 gh_access.py to check gh authentication and repository access, then retry."
    )


def test_gh_failures_report_the_exit_code_and_stderr_with_the_access_next_action() -> (
    None
):
    _gh_failures_report_code_and_stderr()


@workflow_inspect_property(log_cases(), argument="case")
def _log_is_tail_truncated_at_the_byte_budget(case: LogCase) -> None:
    raw = case.text.encode("utf-8")

    observed = run_cli(
        ["log", "9001", f"--max-bytes={case.max_bytes}"], GhReply(0, case.text)
    )

    payload = json.loads(observed.stdout)
    assert observed.exit_code == 0
    assert payload["byte_count"] == len(raw)
    assert payload["truncated"] == (len(raw) > case.max_bytes)
    if len(raw) > case.max_bytes:
        assert payload["log"] == raw[-case.max_bytes :].decode(
            "utf-8", errors="replace"
        )
    else:
        assert payload["log"] == case.text


def test_log_is_truncated_to_the_last_max_bytes_bytes_only_when_larger() -> None:
    _log_is_tail_truncated_at_the_byte_budget()

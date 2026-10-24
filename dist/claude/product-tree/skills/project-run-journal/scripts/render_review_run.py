"""Render a compact inspection surface for a sealed review journal run."""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import subprocess
import sys
from typing import Any, Sequence

import journal_projection as jp

REVIEW_TYPE = "review"
RUN_TOKEN = re.compile(r"^[A-Za-z0-9_-]+$")
RUN_NOT_FOUND_MARKER = "journal run not found"
RECENT_RUN_LIST_LIMIT = "200"


@dataclasses.dataclass(frozen=True)
class RunToken:
    value: str


@dataclasses.dataclass(frozen=True)
class BranchSlug:
    value: str


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a compact summary for a sealed review journal run.",
    )
    parser.add_argument("run_token")
    parser.add_argument(
        "--branch-slug",
        help="Branch slug for a run outside the current branch scope.",
    )
    args = parser.parse_args(argv)

    try:
        run_token = _run_token(args.run_token)
        branch_slug = None
        if args.branch_slug is not None:
            branch_slug = _branch_slug(args.branch_slug)
        result = _render_review_run(run_token, branch_slug=branch_slug)
    except (OSError, RuntimeError) as exc:
        sys.stderr.write(f"failed to run spx journal: {exc}\n")
        return 1
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    try:
        events = _load_events(result.stdout, run_token.value)
        surface = render_summary(run_token.value, events)
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    sys.stdout.write(surface)
    if not surface.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def _render_review_run(
    run_token: RunToken, *, branch_slug: BranchSlug | None = None
) -> subprocess.CompletedProcess[str]:
    if branch_slug is not None:
        return _run_render_command_for_branch(run_token, branch_slug)

    result = _run_render_command(run_token)
    if result.returncode == 0 or RUN_NOT_FOUND_MARKER not in result.stderr:
        return result

    branch_result = _find_run_branch_slug(run_token)
    if branch_result.returncode != 0:
        if branch_result.failure is not None:
            return branch_result.failure
        return result
    if branch_result.branch_slug is None:
        return result
    return _run_render_command_for_branch(run_token, branch_result.branch_slug)


def _run_token(value: str) -> RunToken:
    if not RUN_TOKEN.fullmatch(value):
        offending = "".join(
            sorted({char for char in value if not RUN_TOKEN.fullmatch(char)})
        )
        raise ValueError(
            "run token must contain only ASCII letters, digits, underscores, "
            f"and hyphens; received {value!r} with rejected characters "
            f"{offending!r} (an empty token is also rejected). Pass the "
            "runToken exactly as reported by `spx journal open` or the "
            "review result."
        )
    return RunToken(value)


def _branch_slug(value: str) -> BranchSlug:
    return BranchSlug(value)


def _listed_branch_slug(value: object) -> BranchSlug | None:
    if not isinstance(value, str):
        return None
    return BranchSlug(value)


def _run_render_command(
    run_token: RunToken,
) -> subprocess.CompletedProcess[str]:
    command = [
        "spx",
        "journal",
        "render",
        "--type",
        REVIEW_TYPE,
        "--run",
        run_token.value,
    ]
    return subprocess.run(  # noqa: S603,S607  # NOSONAR - fixed argv, validated token, no shell
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_render_command_for_branch(
    run_token: RunToken,
    branch_slug: BranchSlug,
) -> subprocess.CompletedProcess[str]:
    command = [
        "spx",
        "journal",
        "render",
        "--type",
        REVIEW_TYPE,
        "--run",
        run_token.value,
        "--branch-slug",
        branch_slug.value,
    ]
    return subprocess.run(  # noqa: S603,S607  # NOSONAR - fixed argv, validated args, no shell
        command,
        capture_output=True,
        text=True,
        check=False,
    )


@dataclasses.dataclass(frozen=True)
class BranchLookupResult:
    returncode: int
    branch_slug: BranchSlug | None = None
    failure: subprocess.CompletedProcess[str] | None = None


def _find_run_branch_slug(run_token: RunToken) -> BranchLookupResult:
    result = _run_list_command()
    if result.returncode != 0:
        return BranchLookupResult(returncode=result.returncode, failure=result)
    try:
        runs = _load_listed_runs(result.stdout, run_token.value)
    except ValueError as exc:
        return BranchLookupResult(returncode=1, failure=_lookup_failure(str(exc)))

    matches = [
        branch_slug
        for item in runs
        if item.get("runToken") == run_token.value
        for branch_slug in [_listed_branch_slug(item.get("branchSlug"))]
        if branch_slug is not None
    ]
    if len(matches) != 1:
        return BranchLookupResult(returncode=0)
    return BranchLookupResult(returncode=0, branch_slug=matches[0])


def _lookup_failure(message: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["spx", "journal", "list"],
        returncode=1,
        stdout="",
        stderr=f"{message}\n",
    )


def _run_list_command() -> subprocess.CompletedProcess[str]:
    command = [
        "spx",
        "journal",
        "list",
        "--type",
        REVIEW_TYPE,
        "--sealed",
        "sealed",
        "--limit",
        RECENT_RUN_LIST_LIMIT,
    ]
    return subprocess.run(  # noqa: S603,S607  # NOSONAR - fixed argv, no shell
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def _load_listed_runs(text: str, run_token: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"spx journal list returned invalid JSON: {exc.msg} while looking up "
            f"review run {run_token}. Upgrade `spx` or pass --branch-slug to "
            "skip the lookup."
        ) from exc
    if not isinstance(value, list):
        raise ValueError(
            "spx journal list must return a JSON array while looking up review "
            f"run {run_token}; received {type(value).__name__}. Upgrade `spx` "
            "to a release whose `journal list` prints a JSON array, or pass "
            "--branch-slug to skip the lookup."
        )
    runs: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            runs.append(item)
    return runs


def _load_events(text: str, run_token: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"spx journal render returned invalid JSON: {exc.msg} for review "
            f"run {run_token}. Re-run the command, and upgrade `spx` if the "
            "output stays malformed."
        ) from exc
    if not isinstance(value, list):
        raise ValueError(
            "spx journal render must return a JSON event array for review run "
            f"{run_token}; received {type(value).__name__}. Upgrade `spx` to a "
            "release whose `journal render` prints a JSON event array."
        )
    events: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"event {index} of review run {run_token} must be a JSON object; "
                f"received {type(item).__name__}. Re-run `spx journal render "
                f"--type {REVIEW_TYPE} --run {run_token}` and check the journal "
                "for a corrupted event."
            )
        events.append(item)
    return events


def render_summary(run_token: str, events: list[dict[str, Any]]) -> str:
    terminal = _terminal_event(events)
    if terminal is None:
        seen = ", ".join(sorted({str(event.get("type")) for event in events}))
        raise ValueError(
            f"review run {run_token} has no terminal completion event "
            f"({jp.RUN_COMPLETED!r}); "
            f"received event types [{seen}]. The run is unsealed or truncated: "
            "wait for the review to complete, then re-run this command with "
            "the runToken of a sealed run."
        )

    data = _event_data(terminal, run_token)
    status = _string_value(data, jp.RUN_STATE_STATUS)
    head_sha = _string_value(data, jp.RUN_STATE_HEAD_SHA)
    base_ref = _string_value(data, jp.RUN_STATE_BASE_REF)
    base_sha = _string_value(data, jp.RUN_STATE_BASE_SHA)
    changed_count = _changed_file_count(data)
    examined_count = _scope_advanced_count(events)
    counts = _review_counts(data, events)

    lines = [
        f"Review run: {run_token}",
        f"Status: {status}",
        f"Head: {head_sha}",
        f"Base: {base_ref}{_base_sha_suffix(base_sha)}",
        f"Scope: {changed_count} files, {examined_count} examined",
        f"Findings: {counts['blocking']} blocking, {counts['debt']} debt",
    ]
    if counts["total"] > 0:
        lines.extend(("", jp.render_surface(events)))
    return "\n".join(lines)


def _terminal_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("type") == jp.RUN_COMPLETED:
            return event
    return None


def _event_data(event: dict[str, Any], run_token: str) -> dict[str, Any]:
    data = event.get("data")
    if not isinstance(data, dict):
        raise ValueError(
            f"terminal event data of review run {run_token} must be a JSON "
            f"object; received {type(data).__name__}. Re-run the review so the "
            "run completes with a run-state record."
        )
    return data


def _string_value(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    return value if isinstance(value, str) else ""


def _base_sha_suffix(base_sha: str) -> str:
    if base_sha == "":
        return ""
    return f" @ {base_sha}"


def _changed_file_count(data: dict[str, Any]) -> int:
    scope = data.get(jp.RUN_STATE_SCOPE)
    if not isinstance(scope, dict):
        return 0
    changed_files = scope.get("changedFiles")
    if not isinstance(changed_files, list):
        return 0
    return len(changed_files)


def _scope_advanced_count(events: list[dict[str, Any]]) -> int:
    return sum(1 for event in events if event.get("type") == jp.SCOPE_ADVANCED)


def _review_counts(
    terminal_data: dict[str, Any], events: list[dict[str, Any]]
) -> dict[str, int]:
    review = terminal_data.get("review")
    if isinstance(review, dict):
        blocking = _int_value(review.get("blocking"))
        debt = _int_value(review.get("debt"))
        return {
            "blocking": blocking,
            "debt": debt,
            "total": _finding_event_count(events),
        }

    blocking = 0
    debt = 0
    total = 0
    for event in events:
        if event.get("type") != jp.FINDING_REPORTED:
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        severity = data.get("severity")
        total += 1
        if severity == jp.Severity.REJECT:
            blocking += 1
        elif severity == jp.Severity.WARNING:
            debt += 1
    return {"blocking": blocking, "debt": debt, "total": total}


def _finding_event_count(events: list[dict[str, Any]]) -> int:
    return sum(1 for event in events if event.get("type") == jp.FINDING_REPORTED)


def _int_value(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


if __name__ == "__main__":
    raise SystemExit(main())

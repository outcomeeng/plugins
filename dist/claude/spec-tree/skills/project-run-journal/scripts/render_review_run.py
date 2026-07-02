"""Render a compact inspection surface for a sealed review journal run."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Sequence

import journal_projection as jp

REVIEW_TYPE = "review"
RUN_NOT_FOUND = "journal run not found"
RECENT_RUN_LIST_LIMIT = "200"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a compact summary for a sealed review journal run.",
    )
    parser.add_argument("run_token")
    parser.add_argument(
        "--branch-slug",
        help="Branch slug from `spx journal list` for runs outside the current branch scope.",
    )
    args = parser.parse_args(argv)

    try:
        result = _render_review_run(args.run_token, branch_slug=args.branch_slug)
    except OSError as exc:
        sys.stderr.write(f"failed to run spx journal: {exc}\n")
        return 1
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    try:
        events = _load_events(result.stdout)
        surface = render_summary(args.run_token, events)
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    sys.stdout.write(surface)
    if not surface.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def _render_review_run(
    run_token: str, *, branch_slug: str | None = None
) -> subprocess.CompletedProcess[str]:
    if branch_slug is not None:
        return _run_render_command(run_token, branch_slug=branch_slug)

    result = _run_render_command(run_token)
    if result.returncode == 0 or RUN_NOT_FOUND not in result.stderr:
        return result

    discovered_branch_slug = _branch_slug_for_recent_run(run_token)
    if discovered_branch_slug is None:
        return result
    return _run_render_command(run_token, branch_slug=discovered_branch_slug)


def _run_render_command(
    run_token: str, *, branch_slug: str | None = None
) -> subprocess.CompletedProcess[str]:
    command = [
        "spx",
        "journal",
        "render",
        "--type",
        REVIEW_TYPE,
        "--run",
        run_token,
    ]
    if branch_slug is not None:
        command.extend(["--branch-slug", branch_slug])
    return subprocess.run(  # noqa: S603,S607
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def _branch_slug_for_recent_run(run_token: str) -> str | None:
    result = subprocess.run(  # noqa: S603,S607
        [
            "spx",
            "journal",
            "list",
            "--type",
            REVIEW_TYPE,
            "--limit",
            RECENT_RUN_LIST_LIMIT,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, list):
        return None
    for item in value:
        if not isinstance(item, dict):
            continue
        if item.get("runToken") != run_token:
            continue
        branch_slug = item.get("branchSlug")
        if isinstance(branch_slug, str) and branch_slug != "":
            return branch_slug
    return None


def _load_events(text: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"spx journal render returned invalid JSON: {exc.msg}"
        ) from exc
    if not isinstance(value, list):
        raise ValueError("spx journal render must return a JSON event array")
    events: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"event {index} must be a JSON object")
        events.append(item)
    return events


def render_summary(run_token: str, events: list[dict[str, Any]]) -> str:
    terminal = _terminal_event(events)
    if terminal is None:
        raise ValueError(f"review run {run_token} has no terminal completion event")

    data = _event_data(terminal)
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


def _event_data(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data")
    if not isinstance(data, dict):
        raise ValueError("terminal event data must be a JSON object")
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

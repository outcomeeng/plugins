"""Render a compact inspection surface for a sealed review journal run."""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Protocol, Sequence, cast

import journal_projection as jp

REVIEW_TYPE = "review"
RUN_TOKEN = re.compile(r"^[A-Za-z0-9_-]+$")
_HERE = pathlib.Path(__file__).resolve()
_CHANGESET_SCOPE_PATH = (
    _HERE.parents[2] / "scope-changeset" / "scripts" / "changeset_scope.py"
)


class ChangesetScopeModule(Protocol):
    def branch_slug(
        self, branch_name: str, state_dir: pathlib.Path | None = None
    ) -> str: ...


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
        _validate_run_token(args.run_token)
        if args.branch_slug is not None:
            _validate_branch_slug(args.branch_slug)
        result = _render_review_run(args.run_token, branch_slug=args.branch_slug)
    except OSError as exc:
        sys.stderr.write(f"failed to run spx journal: {exc}\n")
        return 1
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
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
    if result.returncode == 0:
        return result

    return result


def _load_changeset_scope() -> ChangesetScopeModule:
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cast(ChangesetScopeModule, cached)
    spec = importlib.util.spec_from_file_location(
        "changeset_scope", _CHANGESET_SCOPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load changeset_scope from {_CHANGESET_SCOPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return cast(ChangesetScopeModule, module)


def _validate_run_token(value: str) -> None:
    if not RUN_TOKEN.fullmatch(value):
        raise ValueError(
            "run token must contain only ASCII letters, digits, underscores, and hyphens"
        )


def _validate_branch_slug(value: str) -> None:
    if value == "":
        raise ValueError("branch slug must not be empty")
    changeset_scope = _load_changeset_scope()
    if changeset_scope.branch_slug(value) != value:
        raise ValueError("branch slug must be a canonical changeset-scope branch slug")


def _run_render_command(
    run_token: str, *, branch_slug: str | None = None
) -> subprocess.CompletedProcess[str]:
    _validate_run_token(run_token)
    if branch_slug is not None:
        _validate_branch_slug(branch_slug)
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

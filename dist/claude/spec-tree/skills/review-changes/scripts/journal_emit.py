"""Review consumer's run-journal adapter — stdlib only.

Bridges the review-result schema to the shared run-journal projection.
``review_result.py`` remains the policy module for the structured review document;
the run journal records one review run as ``spx journal`` events and derives
the run status from the sealed event prefix through ``journal_projection.py``.

The review streams its events live: it opens the journal, appends a
scope-entered event, appends a scope-advanced event as it examines each
changed file, appends a finding-reported event the instant it raises each
finding, appends a run-completed event, and seals — never a single batch of
events built from a finished result, so a reader resuming from a cursor
watches the run advance. One CLI subcommand builds each domain event so the
consuming skill appends it the moment the run reaches it:

- ``metadata`` derives the run identity from the current worktree and env refs.
- ``scope-entered`` prints the scope-entered event from that metadata.
- ``scope-advanced`` prints a scope-advanced event naming one examined file.
- ``finding-reported`` reads one finding JSON on stdin, parses it through
  ``review_result.parse_finding_json`` (the per-finding validity gate), and
  prints the finding-reported event; a malformed finding exits non-zero
  before any event is printed.
- ``run-completed`` reads the streamed event prefix on stdin, derives the
  terminal status from it, and prints the terminal run-completed event.
- ``render`` reads a sealed event prefix on stdin and prints the shared
  projection's rollup and human-readable surface as JSON.

Review findings map into the shared projection as findings: ``blocking`` is a
rejecting finding, while ``debt`` is a warning finding. A review carries no
decision or verdict field; terminal status belongs to the channel projection
over the recorded event prefix.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from dataclasses import replace
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import review_result as review_schema

_HERE = pathlib.Path(__file__).resolve().parent


def _load_module(name: str, path: pathlib.Path) -> ModuleType:
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


review_result = _load_module("review_result", _HERE / "review_result.py")
compute_diff = _load_module("compute_diff", _HERE / "compute_diff.py")
jp = _load_module(
    "journal_projection",
    _HERE.parents[1] / "project-run-journal" / "scripts" / "journal_projection.py",
)
changeset_scope = _load_module(
    "changeset_scope",
    _HERE.parents[1] / "scope-changeset" / "scripts" / "changeset_scope.py",
)

ENV_BASE_REF = "SPX_VERIFY_BASE_REF"
ENV_HEAD_REF = "SPX_VERIFY_HEAD_REF"
ENV_BRANCH = "SPX_VERIFY_BRANCH"
ENV_TARGET_KIND = "SPX_VERIFY_TARGET_KIND"
ENV_PULL_REQUEST_NUMBER = "SPX_VERIFY_PULL_REQUEST_NUMBER"
DEFAULT_HEAD_REF = "HEAD"
DEFAULT_TARGET = "working-diff"
PARTICIPANTS = ("review",)
REVIEW_PROMPT = pathlib.Path("references") / "review-prompt.md"
MANIFEST_SCHEMA_VERSION = compute_diff.MANIFEST_SCHEMA_VERSION


def _project_severity(severity: object) -> object:
    if str(severity) == "blocking":
        return jp.Severity.REJECT
    if str(severity) == "debt":
        return jp.Severity.WARNING
    raise ValueError(f"unknown review severity {severity!s}")


def _project_finding(finding: review_schema.Finding) -> object:
    # Carry the full review finding into the shared journal Finding: the
    # concern (category) and action (required change) are optional projection
    # fields the review kind populates, so the sealed events are the complete
    # source for the local surface, the hosted PR-review render, and the
    # cross-run fold — none folded into ``message`` and none dropped.
    return jp.Finding(
        file=finding.file,
        line=finding.line,
        rule=finding.rule,
        severity=_project_severity(finding.severity),
        message=finding.message,
        identifier=finding.id,
        concern=str(finding.concern),
        action=finding.action,
    )


def scope_entered_event(metadata: Any, *, now: str, attempt: int) -> dict:
    return jp.scope_entered_event(
        jp.run_from_metadata(metadata), now=now, attempt=attempt
    )


def finding_reported_event(
    finding: review_schema.Finding, *, now: str, attempt: int
) -> dict:
    return jp.finding_reported_event(
        _project_finding(finding), now=now, attempt=attempt
    )


def run_completed_event(
    metadata: Any,
    prefix: list[dict[str, object]],
    *,
    completed_at: str,
    now: str,
    attempt: int,
) -> dict:
    status = jp.terminal_status(jp.compute_overall(prefix))
    run = replace(jp.run_from_metadata(metadata), completed_at=completed_at)
    return jp.run_completed_event(run, status=status, now=now, attempt=attempt)


def render_events(events: list[dict[str, object]]) -> dict[str, str]:
    counts = {"blocking": 0, "debt": 0}
    for event in events:
        if event.get("type") != jp.FINDING_REPORTED:
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        if data.get("severity") == jp.Severity.REJECT:
            counts["blocking"] += 1
        if data.get("severity") == jp.Severity.WARNING:
            counts["debt"] += 1
    return {
        "overall": str(jp.compute_overall(events)),
        "blocking": str(counts["blocking"]),
        "debt": str(counts["debt"]),
        "countLine": f"BLOCKING: {counts['blocking']}, DEBT: {counts['debt']}",
        "surface": str(jp.render_surface(events)),
    }


def _resolve_base_ref() -> str:
    env_value = os.environ.get(ENV_BASE_REF, "").strip()
    if env_value:
        return env_value
    bare_base = changeset_scope.detect_base_ref(pathlib.Path.cwd(), strict=True)
    return str(changeset_scope.remote_tracking_ref(bare_base))


def _resolve_head_ref() -> str:
    return os.environ.get(ENV_HEAD_REF, "").strip() or DEFAULT_HEAD_REF


def _resolve_branch_name() -> str:
    return os.environ.get(ENV_BRANCH, "").strip() or str(
        changeset_scope.detect_current_branch(pathlib.Path.cwd())
    )


def _resolve_target_kind() -> object:
    value = os.environ.get(ENV_TARGET_KIND, "").strip()
    if value == "":
        return jp.JournalTargetKind.BRANCH
    return jp.JournalTargetKind(value)


def _resolve_pull_request_number(target_kind: object) -> int | None:
    value = os.environ.get(ENV_PULL_REQUEST_NUMBER, "").strip()
    if target_kind == jp.JournalTargetKind.PULL_REQUEST:
        if value == "":
            raise ValueError(
                f"{ENV_PULL_REQUEST_NUMBER} is required for pull-request target"
            )
        number = int(value)
        if number <= 0:
            raise ValueError(f"{ENV_PULL_REQUEST_NUMBER} must be positive")
        return number
    if value:
        raise ValueError(f"{ENV_PULL_REQUEST_NUMBER} requires pull-request target")
    return None


def _review_scope(
    *, base_ref: str, head_ref: str, repo: pathlib.Path
) -> dict[str, object]:
    range_spec = f"{base_ref}...{head_ref}"
    changed_files = changeset_scope.expand_diff_range(range_spec, repo=repo)
    review_input = compute_diff.combined_diff(base_ref, head_ref)
    return {
        "baseRef": base_ref,
        "headRef": head_ref,
        "changedFiles": changed_files,
        "reviewInputSha256": hashlib.sha256(review_input.encode("utf-8")).hexdigest(),
    }


def _read_review_manifest(path: pathlib.Path) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"review manifest is invalid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read review manifest {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("review manifest must be a JSON object")
    schema_version = raw.get("schema_version")
    if schema_version != MANIFEST_SCHEMA_VERSION:
        raise ValueError(
            "review manifest schema_version must be "
            f"{MANIFEST_SCHEMA_VERSION}, got {schema_version!r}"
        )
    return raw


def _require_manifest_str(manifest: dict[str, object], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"review manifest {key!r} must be a non-empty string")
    return value


def _manifest_changed_files(manifest: dict[str, object]) -> list[str]:
    sections = manifest.get("sections")
    if not isinstance(sections, list):
        raise ValueError("review manifest 'sections' must be a JSON array")
    changed_files: list[str] = []
    seen: set[str] = set()
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError("review manifest section must be a JSON object")
        files = section.get("files")
        if not isinstance(files, list):
            raise ValueError("review manifest section 'files' must be a JSON array")
        for file_value in files:
            if not isinstance(file_value, str) or file_value == "":
                raise ValueError(
                    "review manifest section 'files' entries must be non-empty strings"
                )
            if file_value in seen:
                continue
            seen.add(file_value)
            changed_files.append(file_value)
    return changed_files


def _review_scope_from_manifest(manifest_path: pathlib.Path) -> dict[str, object]:
    manifest = _read_review_manifest(manifest_path)
    return {
        "baseRef": _require_manifest_str(manifest, "base_ref"),
        "headRef": _require_manifest_str(manifest, "head_ref"),
        "changedFiles": _manifest_changed_files(manifest),
        "reviewInputSha256": _require_manifest_str(manifest, "diff_sha256"),
    }


def _digest(value: object, *, length: int | None = None) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if length is None:
        return digest
    return digest[:length]


def _file_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_config_digest(
    skill_dir: pathlib.Path | None = None,
) -> str:
    root = skill_dir or _HERE.parent
    prompt_path = root / REVIEW_PROMPT
    return _digest(
        {
            "skill": "review-changes",
            "schemaVersion": review_result.SCHEMA_VERSION,
            "projection": "journal_projection",
            "prompt": {
                "path": str(REVIEW_PROMPT),
                "sha256": _file_digest(prompt_path),
            },
        }
    )


def metadata_for_worktree(
    *,
    started_at: str,
    completed_at: str,
    target: str = DEFAULT_TARGET,
    review_manifest_path: pathlib.Path | None = None,
) -> dict[str, object]:
    repo = pathlib.Path.cwd()
    if review_manifest_path is None:
        base_ref = _resolve_base_ref()
        head_ref = _resolve_head_ref()
        scope = _review_scope(base_ref=base_ref, head_ref=head_ref, repo=repo)
    else:
        scope = _review_scope_from_manifest(review_manifest_path)
        base_ref = str(scope["baseRef"])
        head_ref = str(scope["headRef"])
    branch_name = _resolve_branch_name()
    target_kind = _resolve_target_kind()
    pull_request_number = _resolve_pull_request_number(target_kind)
    metadata = {
        "target": target,
        jp.RUN_STATE_SCOPE_HASH: _digest(scope, length=12),
        jp.RUN_STATE_BRANCH_NAME: branch_name,
        jp.RUN_STATE_BRANCH_SLUG: str(changeset_scope.branch_slug(branch_name)),
        jp.RUN_STATE_TARGET_KIND: str(target_kind),
        jp.RUN_STATE_HEAD_SHA: str(changeset_scope.commit_oid(head_ref, repo=repo)),
        jp.RUN_STATE_BASE_REF: base_ref,
        jp.RUN_STATE_BASE_SHA: str(changeset_scope.commit_oid(base_ref, repo=repo)),
        jp.RUN_STATE_CONFIG_DIGEST: review_config_digest(),
        jp.RUN_STATE_PARTICIPANTS: list(PARTICIPANTS),
        jp.RUN_STATE_SCOPE: scope,
        jp.RUN_STATE_STARTED_AT: started_at,
        jp.RUN_STATE_COMPLETED_AT: completed_at,
        jp.RUN_STATE_OUTPUT_PATHS: [],
    }
    if pull_request_number is not None:
        metadata[jp.RUN_STATE_PULL_REQUEST_NUMBER] = pull_request_number
    return metadata


def _emit_event(event: dict) -> int:
    sys.stdout.write(json.dumps(event) + "\n")
    return 0


def _scope_entered(args: argparse.Namespace) -> int:
    try:
        metadata = jp.run_metadata_from_json(args.metadata)
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return _emit_event(
        scope_entered_event(metadata, now=args.now, attempt=args.attempt)
    )


def _scope_advanced(args: argparse.Namespace) -> int:
    return _emit_event(
        jp.scope_advanced_event(args.unit, now=args.now, attempt=args.attempt)
    )


def _finding_reported(args: argparse.Namespace) -> int:
    try:
        finding = review_result.parse_finding_json(sys.stdin.read())
    except (ValueError, review_result.ReviewResultValidationError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return _emit_event(
        finding_reported_event(finding, now=args.now, attempt=args.attempt)
    )


def _run_completed(args: argparse.Namespace) -> int:
    try:
        metadata = jp.run_metadata_from_json(args.metadata)
        prefix = json.load(sys.stdin)
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    if not isinstance(prefix, list):
        sys.stderr.write("event prefix must be a JSON array\n")
        return 1
    return _emit_event(
        run_completed_event(
            metadata,
            prefix,
            completed_at=args.completed_at,
            now=args.now,
            attempt=args.attempt,
        )
    )


def _render() -> int:
    json.dump(render_events(json.load(sys.stdin)), sys.stdout)
    return 0


def _emit_metadata(args: argparse.Namespace) -> int:
    # The run derives its identity at the start, when only the start time is
    # known; the terminal ``run-completed`` event carries the real completion
    # time through its ``--completed-at`` flag, so ``--completed-at`` here
    # defaults to the start time as a provisional value the streaming flow
    # overrides at seal.
    completed_at = args.completed_at or args.started_at
    try:
        metadata = metadata_for_worktree(
            started_at=args.started_at,
            completed_at=completed_at,
            target=args.target,
            review_manifest_path=args.manifest,
        )
    except (
        changeset_scope.BaseRefNotConfiguredError,
        changeset_scope.DetachedHeadError,
        OSError,
        RuntimeError,
        subprocess.CalledProcessError,
        TypeError,
        ValueError,
    ) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    json.dump(metadata, sys.stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def _add_event_args(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--now", required=True, help="UTC timestamp for the event")
        sub.add_argument("--attempt", type=int, default=1, help="run attempt number")

    scope_entered = subparsers.add_parser(
        "scope-entered",
        help="print the scope-entered event opening a streaming review run",
    )
    _add_event_args(scope_entered)
    scope_entered.add_argument("--metadata", required=True, help="metadata JSON object")

    scope_advanced = subparsers.add_parser(
        "scope-advanced",
        help="print a scope-advanced event naming one examined changed file",
    )
    _add_event_args(scope_advanced)
    scope_advanced.add_argument("--unit", required=True, help="the examined unit")

    finding_reported = subparsers.add_parser(
        "finding-reported",
        help="parse one finding JSON (stdin) and print its finding-reported event",
    )
    _add_event_args(finding_reported)

    run_completed = subparsers.add_parser(
        "run-completed",
        help="print the terminal run-completed event from the streamed prefix (stdin)",
    )
    _add_event_args(run_completed)
    run_completed.add_argument("--metadata", required=True, help="metadata JSON object")
    run_completed.add_argument(
        "--completed-at", required=True, help="UTC run completion timestamp"
    )

    subparsers.add_parser(
        "render",
        help="roll up and render a sealed event prefix to a review surface",
    )

    metadata = subparsers.add_parser(
        "metadata",
        help="derive review journal metadata from the current worktree",
    )
    metadata.add_argument("--started-at", required=True)
    metadata.add_argument("--completed-at", default="")
    metadata.add_argument("--target", default=DEFAULT_TARGET)
    metadata.add_argument(
        "--manifest",
        type=pathlib.Path,
        default=None,
        help="computed review bundle manifest.json to derive the exact reviewed scope",
    )

    args = parser.parse_args(argv)
    handlers = {
        "scope-entered": _scope_entered,
        "scope-advanced": _scope_advanced,
        "finding-reported": _finding_reported,
        "run-completed": _run_completed,
        "metadata": _emit_metadata,
    }
    handler = handlers.get(args.command)
    if handler is not None:
        return handler(args)
    return _render()


if __name__ == "__main__":
    raise SystemExit(main())

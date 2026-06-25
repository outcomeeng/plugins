"""Review consumer's run-journal adapter — stdlib only.

Bridges the review-result schema to the shared run-journal projection.
``review_result.py`` remains the arbiter for the structured review document;
the run journal records one review run as ``spx journal`` events and derives
the run status from the sealed event prefix through ``journal_projection.py``.

Two CLI subcommands drive the stateless local emit:

- ``build-events`` reads a review-result JSON document on stdin and prints
  ordered ``spx journal`` channel event inputs, one JSON object per line.
- ``render`` reads a sealed event prefix on stdin and prints the shared
  projection's rollup and human-readable surface as JSON.

Review findings map into the shared projection as findings: ``blocking`` is a
rejecting finding, while ``debt`` is a warning finding. The review-result
itself still carries no decision or verdict field; terminal status belongs to
the channel projection over the recorded event prefix.
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
from dataclasses import dataclass
from types import ModuleType
from typing import TYPE_CHECKING, Any, Mapping, cast

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
RENDER_TEMPLATES = pathlib.Path("references") / "render"


@dataclass(frozen=True)
class ReviewRunMetadata:
    target: str
    scope_hash: str
    branch_name: str
    branch_slug: str
    head_sha: str
    base_ref: str
    base_sha: str
    config_digest: str
    participants: tuple[str, ...]
    scope: Mapping[str, Any]
    started_at: str
    completed_at: str
    output_paths: tuple[str, ...] = ()
    target_kind: object = None
    pull_request_number: int | None = None


def _project_severity(severity: object) -> object:
    if str(severity) == "blocking":
        return jp.Severity.REJECT
    if str(severity) == "debt":
        return jp.Severity.WARNING
    raise ValueError(f"unknown review severity {severity!s}")


def _project_finding(finding: review_schema.Finding) -> object:
    return jp.Finding(
        file=finding.file,
        line=finding.line,
        rule=finding.rule,
        severity=_project_severity(finding.severity),
        message=f"{finding.message} Required: {finding.action}",
    )


def events_for_review(
    result: review_schema.ReviewResult,
    metadata: ReviewRunMetadata,
    *,
    now: str,
    attempt: int = 1,
) -> list[dict[str, object]]:
    run = jp.RunResult(
        target=metadata.target,
        scope_hash=metadata.scope_hash,
        branch_name=metadata.branch_name,
        branch_slug=metadata.branch_slug,
        head_sha=metadata.head_sha,
        base_ref=metadata.base_ref,
        base_sha=metadata.base_sha,
        config_digest=metadata.config_digest,
        participants=metadata.participants,
        scope=metadata.scope,
        started_at=metadata.started_at,
        completed_at=metadata.completed_at,
        output_paths=metadata.output_paths,
        findings=tuple(_project_finding(finding) for finding in result.findings),
        target_kind=(
            jp.JournalTargetKind.BRANCH
            if metadata.target_kind is None
            else jp.JournalTargetKind(metadata.target_kind)
        ),
        pull_request_number=metadata.pull_request_number,
    )
    return cast(
        "list[dict[str, object]]", jp.build_events(run, now=now, attempt=attempt)
    )


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


def _json_object(text: str, *, name: str) -> dict[str, Any]:
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _json_string_array(text: str, *, name: str) -> tuple[str, ...]:
    value = json.loads(text)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"{name} must be a JSON array of non-empty strings")
    return tuple(value)


def _metadata_from_args(args: argparse.Namespace) -> ReviewRunMetadata:
    return _metadata_from_json(args.metadata)


def _metadata_from_json(text: str) -> ReviewRunMetadata:
    data = _json_object(text, name="metadata")
    return ReviewRunMetadata(
        target=_required_string(data, "target"),
        scope_hash=_required_string(data, jp.RUN_STATE_SCOPE_HASH),
        branch_name=_required_string(data, jp.RUN_STATE_BRANCH_NAME),
        branch_slug=_required_string(data, jp.RUN_STATE_BRANCH_SLUG),
        head_sha=_required_string(data, jp.RUN_STATE_HEAD_SHA),
        base_ref=_required_string(data, jp.RUN_STATE_BASE_REF),
        base_sha=_required_string(data, jp.RUN_STATE_BASE_SHA),
        config_digest=_required_string(data, jp.RUN_STATE_CONFIG_DIGEST),
        participants=_required_string_tuple(data, jp.RUN_STATE_PARTICIPANTS),
        scope=_required_mapping(data, jp.RUN_STATE_SCOPE),
        started_at=_required_string(data, jp.RUN_STATE_STARTED_AT),
        completed_at=_required_string(data, jp.RUN_STATE_COMPLETED_AT),
        output_paths=_optional_string_tuple(data, jp.RUN_STATE_OUTPUT_PATHS),
        target_kind=_required_string(data, jp.RUN_STATE_TARGET_KIND),
        pull_request_number=_optional_positive_int(
            data, jp.RUN_STATE_PULL_REQUEST_NUMBER
        ),
    )


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"metadata {key!r} must be a non-empty string")
    return value


def _required_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"metadata {key!r} must be a JSON object")
    return value


def _required_string_tuple(data: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"metadata {key!r} must be a JSON array of non-empty strings")
    return tuple(value)


def _optional_string_tuple(data: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"metadata {key!r} must be a JSON array of non-empty strings")
    return tuple(value)


def _optional_positive_int(data: Mapping[str, Any], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"metadata {key!r} must be a positive integer when present")
    return value


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


def _digest(value: object, *, length: int | None = None) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if length is None:
        return digest
    return digest[:length]


def _file_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_config_digest(skill_dir: pathlib.Path | None = None) -> str:
    root = skill_dir or _HERE.parent
    prompt_path = root / REVIEW_PROMPT
    render_dir = root / RENDER_TEMPLATES
    template_paths = sorted(path for path in render_dir.glob("*.md") if path.is_file())
    return _digest(
        {
            "skill": "review-changes",
            "schemaVersion": review_result.SCHEMA_VERSION,
            "projection": "journal_projection",
            "prompt": {
                "path": str(REVIEW_PROMPT),
                "sha256": _file_digest(prompt_path),
            },
            "renderTemplates": [
                {
                    "path": str(path.relative_to(root)),
                    "sha256": _file_digest(path),
                }
                for path in template_paths
            ],
        }
    )


def metadata_for_worktree(
    *, started_at: str, completed_at: str, target: str = DEFAULT_TARGET
) -> dict[str, object]:
    repo = pathlib.Path.cwd()
    base_ref = _resolve_base_ref()
    head_ref = _resolve_head_ref()
    branch_name = _resolve_branch_name()
    target_kind = _resolve_target_kind()
    pull_request_number = _resolve_pull_request_number(target_kind)
    scope = _review_scope(base_ref=base_ref, head_ref=head_ref, repo=repo)
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


def _build_events(args: argparse.Namespace) -> int:
    try:
        result = review_result.parse_json(sys.stdin.read())
        metadata = _metadata_from_args(args)
        events = events_for_review(result, metadata, now=args.now, attempt=args.attempt)
    except (ValueError, review_result.ReviewResultValidationError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    for event in events:
        sys.stdout.write(json.dumps(event) + "\n")
    return 0


def _render() -> int:
    json.dump(render_events(json.load(sys.stdin)), sys.stdout)
    return 0


def _emit_metadata(args: argparse.Namespace) -> int:
    try:
        metadata = metadata_for_worktree(
            started_at=args.started_at,
            completed_at=args.completed_at,
            target=args.target,
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

    build = subparsers.add_parser(
        "build-events",
        help="map a review-result JSON document to spx journal event inputs",
    )
    build.add_argument("--now", required=True, help="UTC timestamp for every event")
    build.add_argument("--attempt", type=int, default=1, help="run attempt number")
    build.add_argument("--metadata", required=True, help="metadata JSON object")

    subparsers.add_parser(
        "render",
        help="roll up and render a sealed event prefix to a review surface",
    )

    metadata = subparsers.add_parser(
        "metadata",
        help="derive review journal metadata from the current worktree",
    )
    metadata.add_argument("--started-at", required=True)
    metadata.add_argument("--completed-at", required=True)
    metadata.add_argument("--target", default=DEFAULT_TARGET)

    args = parser.parse_args(argv)
    if args.command == "build-events":
        return _build_events(args)
    if args.command == "metadata":
        return _emit_metadata(args)
    return _render()


if __name__ == "__main__":
    raise SystemExit(main())

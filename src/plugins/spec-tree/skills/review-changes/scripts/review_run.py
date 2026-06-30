"""Single command surface for streaming review runs.

The skill invokes only this runner. The runner owns diff-bundle scratch
storage, journal command invocation, state passing between verbs, and sealing
the journal run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from types import ModuleType
from typing import Any

_HERE = pathlib.Path(__file__).resolve().parent
_SKILL_DIR = _HERE.parent
_SKILLS_DIR = _SKILL_DIR.parent
_REVIEW_PROMPT = pathlib.Path("references") / "review-prompt.md"
_REVIEW_OVERRIDE = pathlib.Path("REVIEW.md")
_STATE_FILENAME = "state.json"
_REVIEW_TYPE = "review"
_DEFAULT_TARGET = "working-diff"
_PARTICIPANTS = ("review",)

ENV_BRANCH = "SPX_VERIFY_BRANCH"
ENV_TARGET_KIND = "SPX_VERIFY_TARGET_KIND"
ENV_PULL_REQUEST_NUMBER = "SPX_VERIFY_PULL_REQUEST_NUMBER"


def _load_module(name: str, path: pathlib.Path) -> ModuleType:
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compute_diff = _load_module("compute_diff", _HERE / "compute_diff.py")
jp = _load_module(
    "journal_projection",
    _SKILLS_DIR / "project-run-journal" / "scripts" / "journal_projection.py",
)
changeset_scope = _load_module(
    "changeset_scope",
    _SKILLS_DIR / "scope-changeset" / "scripts" / "changeset_scope.py",
)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: object, *, length: int | None = None) -> str:
    digest = hashlib.sha256(_json_dumps(value).encode("utf-8")).hexdigest()
    if length is None:
        return digest
    return digest[:length]


def _file_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _optional_file_config(
    root: pathlib.Path, relative_path: pathlib.Path
) -> dict[str, str] | None:
    path = root / relative_path
    if not path.is_file():
        return None
    return {"path": str(relative_path), "sha256": _file_digest(path)}


def _repo_root(repo: pathlib.Path) -> pathlib.Path:
    result = subprocess.run(  # noqa: S603,S607
        ["git", "rev-parse", "--show-toplevel"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return pathlib.Path(result.stdout.strip()).resolve()


def _review_config_digest(repo_root: pathlib.Path) -> str:
    prompt_path = _SKILL_DIR / _REVIEW_PROMPT
    return _digest(
        {
            "skill": "review-changes",
            "runner": "review_run.py",
            "projection": "journal_projection",
            "prompt": {
                "path": str(_REVIEW_PROMPT),
                "sha256": _file_digest(prompt_path),
            },
            "repositoryReviewPolicy": _optional_file_config(
                repo_root, _REVIEW_OVERRIDE
            ),
        }
    )


def _read_json_file(path: pathlib.Path, *, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is invalid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read {name} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _manifest_changed_files(manifest: dict[str, Any]) -> list[str]:
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
            raise ValueError("review manifest section 'files' must be an array")
        for file_value in files:
            if not isinstance(file_value, str) or file_value == "":
                raise ValueError(
                    "review manifest file entries must be non-empty strings"
                )
            if file_value not in seen:
                seen.add(file_value)
                changed_files.append(file_value)
    return changed_files


def _require_manifest_str(manifest: dict[str, Any], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"review manifest {key!r} must be a non-empty string")
    return value


def _target_kind() -> object:
    value = os.environ.get(ENV_TARGET_KIND, "").strip()
    if value == "":
        return jp.JournalTargetKind.BRANCH
    return jp.JournalTargetKind(value)


def _pull_request_number(target_kind: object) -> int | None:
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


def _metadata_from_manifest(
    *, manifest_path: pathlib.Path, started_at: str, target: str
) -> dict[str, Any]:
    repo = pathlib.Path.cwd()
    root = _repo_root(repo)
    manifest = _read_json_file(manifest_path, name="review manifest")
    base_ref = _require_manifest_str(manifest, "base_ref")
    head_ref = _require_manifest_str(manifest, "head_ref")
    scope = {
        "baseRef": base_ref,
        "headRef": head_ref,
        "changedFiles": _manifest_changed_files(manifest),
        "reviewInputSha256": _require_manifest_str(manifest, "diff_sha256"),
    }
    branch_name = os.environ.get(ENV_BRANCH, "").strip() or str(
        changeset_scope.detect_current_branch(repo)
    )
    target_kind = _target_kind()
    metadata: dict[str, Any] = {
        "target": target,
        jp.RUN_STATE_SCOPE_HASH: _digest(scope, length=12),
        jp.RUN_STATE_BRANCH_NAME: branch_name,
        jp.RUN_STATE_BRANCH_SLUG: str(changeset_scope.branch_slug(branch_name)),
        jp.RUN_STATE_TARGET_KIND: str(target_kind),
        jp.RUN_STATE_HEAD_SHA: str(changeset_scope.commit_oid(head_ref, repo=repo)),
        jp.RUN_STATE_BASE_REF: base_ref,
        jp.RUN_STATE_BASE_SHA: str(changeset_scope.commit_oid(base_ref, repo=repo)),
        jp.RUN_STATE_CONFIG_DIGEST: _review_config_digest(root),
        jp.RUN_STATE_PARTICIPANTS: list(_PARTICIPANTS),
        jp.RUN_STATE_SCOPE: scope,
        jp.RUN_STATE_STARTED_AT: started_at,
        jp.RUN_STATE_COMPLETED_AT: started_at,
        jp.RUN_STATE_OUTPUT_PATHS: [],
    }
    pull_request_number = _pull_request_number(target_kind)
    if pull_request_number is not None:
        metadata[jp.RUN_STATE_PULL_REQUEST_NUMBER] = pull_request_number
    return metadata


def _run_journal(
    *args: str, stdin: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603,S607
        ["spx", "journal", *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def _propagate_failure(result: subprocess.CompletedProcess[str]) -> int | None:
    if result.returncode == 0:
        return None
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode or 1


def _journal_json(
    *args: str, stdin: str | None = None
) -> tuple[int, object | None, str]:
    result = _run_journal(*args, stdin=stdin)
    failed = _propagate_failure(result)
    if failed is not None:
        return failed, None, result.stdout
    try:
        return 0, json.loads(result.stdout), result.stdout
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"spx journal returned invalid JSON: {exc.msg}\n")
        return 1, None, result.stdout


def _append_event(run_token: str, event: dict[str, object]) -> int:
    result = _run_journal(
        "append",
        "--type",
        _REVIEW_TYPE,
        "--run",
        run_token,
        stdin=json.dumps(event),
    )
    failed = _propagate_failure(result)
    if failed is not None:
        return failed
    return 0


def _state_path(scratch_dir: pathlib.Path) -> pathlib.Path:
    return scratch_dir / _STATE_FILENAME


def _write_state(state: dict[str, object]) -> pathlib.Path:
    scratch_dir = pathlib.Path(str(state["scratchDir"]))
    path = _state_path(scratch_dir)
    path.write_text(
        json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return path


def _read_state(path: pathlib.Path) -> dict[str, Any]:
    state = _read_json_file(path, name="review runner state")
    run_token = state.get("runToken")
    if not isinstance(run_token, str) or run_token == "":
        raise ValueError("review runner state missing non-empty runToken")
    metadata = state.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("review runner state missing metadata object")
    return state


def _finding_severity(value: object) -> object:
    text = str(value)
    if text == "blocking":
        return jp.Severity.REJECT
    if text == "debt":
        return jp.Severity.WARNING
    if text in {severity.value for severity in jp.Severity}:
        return jp.Severity(text)
    return jp.Severity.UNKNOWN


def _optional_str(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _line_number(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _finding_event_from_stdin(*, now: str, attempt: int) -> dict[str, object]:
    try:
        raw = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        raise ValueError(f"finding input is invalid JSON: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ValueError("finding input must be a JSON object")
    finding = jp.Finding(
        file=str(raw.get("file", "")),
        line=_line_number(raw.get("line")),
        rule=str(raw.get("rule", "")),
        severity=_finding_severity(raw.get("severity", "")),
        message=str(raw.get("message", "")),
        identifier=_optional_str(raw.get("id")),
        concern=_optional_str(raw.get("concern")),
        action=_optional_str(raw.get("action")),
    )
    return jp.finding_reported_event(finding, now=now, attempt=attempt)


def _completed_event(
    *, metadata: dict[str, Any], prefix: list[dict[str, object]], completed_at: str
) -> dict[str, object]:
    parsed = jp.run_metadata_from_json(json.dumps(metadata))
    run = replace(jp.run_from_metadata(parsed), completed_at=completed_at)
    overall = jp.compute_overall(prefix)
    status = jp.terminal_status(overall)
    event = jp.run_completed_event(run, status=status, now=completed_at)
    data = event.get("data")
    if isinstance(data, dict):
        data["review"] = {
            "blocking": _finding_counts(prefix)["blocking"],
            "debt": _finding_counts(prefix)["debt"],
            "overall": str(overall),
        }
    return event


def _finding_counts(events: list[dict[str, object]]) -> dict[str, int]:
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
    return counts


def _cleanup_state(state_path: pathlib.Path) -> None:
    scratch_dir = state_path.resolve().parent
    temp_root = pathlib.Path(tempfile.gettempdir()).resolve()
    try:
        scratch_dir.relative_to(temp_root)
    except ValueError:
        return
    if scratch_dir.name.startswith("review-changes-") and scratch_dir.is_dir():
        shutil.rmtree(scratch_dir)


def _start(args: argparse.Namespace) -> int:
    started_at = _utc_now()
    scratch_dir = pathlib.Path(tempfile.mkdtemp(prefix="review-changes-"))
    try:
        summary = compute_diff.write_bundle(
            base_ref=compute_diff.resolve_base_ref(),
            head_ref=compute_diff.resolve_head_ref(),
            bundle_dir=scratch_dir,
        )
        manifest_path = pathlib.Path(str(summary["manifest_path"]))
        metadata = _metadata_from_manifest(
            manifest_path=manifest_path,
            started_at=started_at,
            target=args.target,
        )
        code, opened, _raw = _journal_json("open", "--type", _REVIEW_TYPE)
        if code != 0:
            shutil.rmtree(scratch_dir)
            return code
        if not isinstance(opened, dict) or not isinstance(opened.get("runToken"), str):
            shutil.rmtree(scratch_dir)
            sys.stderr.write("spx journal open did not return runToken\n")
            return 1
        run_token = str(opened["runToken"])
        event = jp.scope_entered_event(
            jp.run_from_metadata(jp.run_metadata_from_json(json.dumps(metadata))),
            now=started_at,
        )
        code = _append_event(run_token, event)
        if code != 0:
            shutil.rmtree(scratch_dir)
            return code
        state: dict[str, object] = {
            "runToken": run_token,
            "startedAt": started_at,
            "scratchDir": str(scratch_dir),
            "diffPath": str(summary["diff_path"]),
            "manifestPath": str(manifest_path),
            "metadata": metadata,
        }
        state_path = _write_state(state)
        manifest = _read_json_file(manifest_path, name="review manifest")
        output = {
            "runToken": run_token,
            "statePath": str(state_path),
            "diffPath": str(summary["diff_path"]),
            "manifestPath": str(manifest_path),
            "changedFiles": _manifest_changed_files(manifest),
        }
        json.dump(output, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (
        OSError,
        RuntimeError,
        subprocess.CalledProcessError,
        TypeError,
        ValueError,
    ) as exc:
        if scratch_dir.is_dir():
            shutil.rmtree(scratch_dir)
        sys.stderr.write(f"{exc}\n")
        return 1


def _append_scope(args: argparse.Namespace) -> int:
    try:
        state = _read_state(args.state)
        event = jp.scope_advanced_event(args.unit, now=_utc_now())
    except (OSError, TypeError, ValueError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    code = _append_event(str(state["runToken"]), event)
    if code != 0:
        return code
    json.dump({"appended": "scope", "unit": args.unit}, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _append_finding(args: argparse.Namespace) -> int:
    try:
        state = _read_state(args.state)
        event = _finding_event_from_stdin(now=_utc_now(), attempt=1)
    except (OSError, TypeError, ValueError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    code = _append_event(str(state["runToken"]), event)
    if code != 0:
        return code
    json.dump({"appended": "finding"}, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _finish(args: argparse.Namespace) -> int:
    try:
        state = _read_state(args.state)
        run_token = str(state["runToken"])
        code, prefix_value, _raw = _journal_json(
            "read", "--type", _REVIEW_TYPE, "--run", run_token, "--from", "0"
        )
        if code != 0:
            return code
        if not isinstance(prefix_value, list):
            sys.stderr.write("spx journal read output must be a JSON event array\n")
            return 1
        prefix = [event for event in prefix_value if isinstance(event, dict)]
        completed_at = _utc_now()
        event = _completed_event(
            metadata=state["metadata"],
            prefix=prefix,
            completed_at=completed_at,
        )
        code = _append_event(run_token, event)
        if code != 0:
            return code
        sealed = _run_journal("seal", "--type", _REVIEW_TYPE, "--run", run_token)
        failed = _propagate_failure(sealed)
        if failed is not None:
            return failed
        sys.stdout.write(f"{run_token}\n")
        _cleanup_state(args.state)
        return 0
    except (OSError, TypeError, ValueError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="start a review run")
    start.add_argument("--target", default=_DEFAULT_TARGET)

    append_scope = subparsers.add_parser(
        "append-scope", help="append one examined scope unit"
    )
    append_scope.add_argument("--state", type=pathlib.Path, required=True)
    append_scope.add_argument("unit")

    append_finding = subparsers.add_parser(
        "append-finding", help="append one finding read from stdin"
    )
    append_finding.add_argument("--state", type=pathlib.Path, required=True)

    finish = subparsers.add_parser("finish", help="finish and seal the run")
    finish.add_argument("--state", type=pathlib.Path, required=True)

    args = parser.parse_args(argv)
    handlers = {
        "start": _start,
        "append-scope": _append_scope,
        "append-finding": _append_finding,
        "finish": _finish,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())

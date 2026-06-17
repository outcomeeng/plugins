"""Inspect GitHub Actions workflow runs, jobs, logs, checks, and artifacts.

Usage:
    python3 workflow_inspect.py runs [--branch BRANCH] [--limit N]
    python3 workflow_inspect.py run <run-id>
    python3 workflow_inspect.py jobs <run-id>
    python3 workflow_inspect.py log <run-id> [--failed] [--max-bytes N]
    python3 workflow_inspect.py checks <pr-number>
    python3 workflow_inspect.py artifacts <run-id>
    python3 workflow_inspect.py workflow-files

Each subcommand returns JSON on stdout. The `log` subcommand returns the raw
log text inside a `log` field (not JSON-structured) and preserves whitespace
exactly as `gh` emits it; output exceeding `--max-bytes` is truncated to the
last N bytes with `truncated: true` in the response.

Subprocess invocations use `subprocess.run(..., capture_output=True, text=True)`
with bounded lifetime — no streaming gh subcommands, no polling.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

SCHEMA_VERSION = 1
DEFAULT_LOG_MAX_BYTES = 100_000
SUBPROCESS_TIMEOUT_SECONDS = 60


def _run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"subprocess timed out after {exc.timeout}s: {' '.join(cmd)}"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _run_raw(cmd: list[str]) -> tuple[int, str, str]:
    """Like `_run` but preserves stdout whitespace verbatim (for log content)."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"subprocess timed out after {exc.timeout}s: {' '.join(cmd)}"
    return proc.returncode, proc.stdout, proc.stderr.strip()


def _gh_json(args: list[str]) -> tuple[int, Any, str]:
    code, out, err = _run(args)
    if code != 0:
        return code, None, err or out
    try:
        return code, json.loads(out), ""
    except json.JSONDecodeError as exc:
        return 1, None, f"could not parse gh JSON output: {exc}"


def cmd_runs(branch: str | None, limit: int) -> dict[str, Any]:
    args = [
        "gh",
        "run",
        "list",
        "--limit",
        str(limit),
        "--json",
        "databaseId,status,conclusion,workflowName,headBranch,headSha,createdAt,event",
    ]
    if branch:
        args.extend(["--branch", branch])
    code, data, err = _gh_json(args)
    if code != 0 or data is None:
        return {"schema_version": SCHEMA_VERSION, "runs": [], "error": err}
    return {"schema_version": SCHEMA_VERSION, "runs": data, "error": None}


def cmd_run(run_id: str) -> dict[str, Any]:
    fields = (
        "databaseId,status,conclusion,workflowName,headBranch,headSha,createdAt,jobs"
    )
    code, data, err = _gh_json(["gh", "run", "view", run_id, "--json", fields])
    if code != 0 or not isinstance(data, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "error": err or "gh run view returned no run object",
        }
    jobs = data.get("jobs") or []
    return {
        "schema_version": SCHEMA_VERSION,
        "databaseId": data.get("databaseId"),
        "status": data.get("status"),
        "conclusion": data.get("conclusion"),
        "workflowName": data.get("workflowName"),
        "headBranch": data.get("headBranch"),
        "headSha": data.get("headSha"),
        "createdAt": data.get("createdAt"),
        "jobs": [
            {
                "databaseId": job.get("databaseId"),
                "name": job.get("name"),
                "status": job.get("status"),
                "conclusion": job.get("conclusion"),
            }
            for job in jobs
        ],
        "error": None,
    }


def cmd_jobs(run_id: str) -> dict[str, Any]:
    code, data, err = _gh_json(["gh", "run", "view", run_id, "--json", "jobs"])
    if code != 0 or not isinstance(data, dict):
        return {"schema_version": SCHEMA_VERSION, "jobs": [], "error": err}
    jobs = data.get("jobs") or []
    return {
        "schema_version": SCHEMA_VERSION,
        "jobs": [
            {
                "databaseId": job.get("databaseId"),
                "name": job.get("name"),
                "status": job.get("status"),
                "conclusion": job.get("conclusion"),
                "startedAt": job.get("startedAt"),
                "completedAt": job.get("completedAt"),
            }
            for job in jobs
        ],
        "error": None,
    }


def cmd_log(run_id: str, failed: bool, max_bytes: int) -> dict[str, Any]:
    """Return the run log truncated to the last `max_bytes` bytes.

    Tail-truncated rather than head-truncated: CI failures appear at the end
    of a run, so keeping the trailing window preserves the diagnostic content.
    """
    args = ["gh", "run", "view", run_id]
    args.append("--log-failed" if failed else "--log")
    code, out, err = _run_raw(args)
    if code != 0:
        return {
            "schema_version": SCHEMA_VERSION,
            "log": "",
            "failed_only": failed,
            "byte_count": 0,
            "truncated": False,
            "error": err or "gh run view --log returned non-zero",
        }
    raw = out.encode("utf-8")
    byte_count = len(raw)
    truncated = byte_count > max_bytes
    if truncated:
        # Take the last `max_bytes` (most recent log content); decode with
        # `errors="replace"` to absorb any partial multi-byte char at the boundary.
        log_text = raw[-max_bytes:].decode("utf-8", errors="replace")
    else:
        log_text = out
    return {
        "schema_version": SCHEMA_VERSION,
        "log": log_text,
        "failed_only": failed,
        "byte_count": byte_count,
        "truncated": truncated,
        "error": None,
    }


def cmd_checks(pr_number: str) -> dict[str, Any]:
    code, data, err = _gh_json(
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--json",
            "number,headRefName,statusCheckRollup",
        ]
    )
    if code != 0 or not isinstance(data, dict):
        return {"schema_version": SCHEMA_VERSION, "error": err}
    return {
        "schema_version": SCHEMA_VERSION,
        "number": data.get("number"),
        "headRefName": data.get("headRefName"),
        "statusCheckRollup": data.get("statusCheckRollup"),
        "error": None,
    }


def cmd_artifacts(run_id: str) -> dict[str, Any]:
    # archive_download_url is a presigned URL with embedded credentials; never
    # surface it through the agent. Callers that need to download an artifact
    # invoke `gh run download <run-id>` directly.
    code, data, err = _gh_json(
        [
            "gh",
            "api",
            f"repos/:owner/:repo/actions/runs/{run_id}/artifacts",
            "--jq",
            "{artifacts: [.artifacts[] | {id, name, size_in_bytes, expired}]}",
        ]
    )
    if code != 0 or not isinstance(data, dict):
        return {"schema_version": SCHEMA_VERSION, "artifacts": [], "error": err}
    return {
        "schema_version": SCHEMA_VERSION,
        "artifacts": data.get("artifacts", []),
        "error": None,
    }


def cmd_workflow_files() -> dict[str, Any]:
    code, data, err = _gh_json(
        [
            "gh",
            "workflow",
            "list",
            "--json",
            "id,name,state,path",
        ]
    )
    if code != 0 or not isinstance(data, list):
        return {"schema_version": SCHEMA_VERSION, "workflows": [], "error": err}
    return {"schema_version": SCHEMA_VERSION, "workflows": data, "error": None}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Inspect GitHub Actions state.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_runs = sub.add_parser("runs", help="list recent workflow runs")
    p_runs.add_argument("--branch", help="filter runs by branch")
    p_runs.add_argument("--limit", type=int, default=10, help="maximum runs to return")

    p_run = sub.add_parser("run", help="view a workflow run with its jobs")
    p_run.add_argument("run_id")

    p_jobs = sub.add_parser("jobs", help="list jobs for a run")
    p_jobs.add_argument("run_id")

    p_log = sub.add_parser("log", help="fetch run logs")
    p_log.add_argument("run_id")
    p_log.add_argument("--failed", action="store_true", help="failed-step logs only")
    p_log.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_LOG_MAX_BYTES,
        help=f"truncate log to the last N bytes (default {DEFAULT_LOG_MAX_BYTES})",
    )

    p_checks = sub.add_parser("checks", help="fetch PR check rollup")
    p_checks.add_argument("pr_number")

    p_artifacts = sub.add_parser("artifacts", help="list artifacts for a run")
    p_artifacts.add_argument("run_id")

    sub.add_parser("workflow-files", help="list workflow definitions")

    args = parser.parse_args(argv[1:])

    if args.cmd == "runs":
        result = cmd_runs(args.branch, args.limit)
    elif args.cmd == "run":
        result = cmd_run(args.run_id)
    elif args.cmd == "jobs":
        result = cmd_jobs(args.run_id)
    elif args.cmd == "log":
        result = cmd_log(args.run_id, args.failed, args.max_bytes)
    elif args.cmd == "checks":
        result = cmd_checks(args.pr_number)
    elif args.cmd == "artifacts":
        result = cmd_artifacts(args.run_id)
    else:
        # `workflow-files` is the only remaining subcommand; argparse with
        # `required=True` rejects anything else before reaching this branch.
        result = cmd_workflow_files()

    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0 if result.get("error") is None else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

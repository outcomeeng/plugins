"""Inspect GitHub Actions workflow runs, jobs, logs, checks, and artifacts.

Usage:
    uv run python workflow_inspect.py runs [--branch BRANCH] [--limit N]
    uv run python workflow_inspect.py run <run-id>
    uv run python workflow_inspect.py jobs <run-id>
    uv run python workflow_inspect.py log <run-id> [--failed]
    uv run python workflow_inspect.py checks <pr-number>
    uv run python workflow_inspect.py artifacts <run-id>
    uv run python workflow_inspect.py workflow-files

Each subcommand returns JSON on stdout. The `log` subcommand returns the raw
log text inside a `log` field (not JSON-structured).

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


def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


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


def cmd_log(run_id: str, failed: bool) -> dict[str, Any]:
    args = ["gh", "run", "view", run_id]
    args.append("--log-failed" if failed else "--log")
    code, out, err = _run(args)
    if code != 0:
        return {
            "schema_version": SCHEMA_VERSION,
            "log": "",
            "failed_only": failed,
            "error": err or "gh run view --log returned non-zero",
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "log": out,
        "failed_only": failed,
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
    code, data, err = _gh_json(
        [
            "gh",
            "api",
            f"repos/:owner/:repo/actions/runs/{run_id}/artifacts",
            "--jq",
            "{artifacts: [.artifacts[] | {id, name, size_in_bytes, archive_download_url, expired}]}",
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
        result = cmd_log(args.run_id, args.failed)
    elif args.cmd == "checks":
        result = cmd_checks(args.pr_number)
    elif args.cmd == "artifacts":
        result = cmd_artifacts(args.run_id)
    elif args.cmd == "workflow-files":
        result = cmd_workflow_files()
    else:
        parser.error(f"unknown subcommand: {args.cmd}")
        return 2

    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0 if result.get("error") is None else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

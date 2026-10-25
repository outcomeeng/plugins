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

A run id or pull request number that is not a positive integer, a dash-led
token such as `--5` or `-abc` included, is rejected before any `gh` call.

Failures set `error` to `<subcommand> <argument>: <cause>. Next: <action>.` and
exit 1. Every `gh` call goes through the module-level `_run` function.

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
POSITIONAL_PLACEHOLDER = "0"
# Subcommands that take one positional number, with the long options each
# accepts and the subset of those that consume the following token as a value.
POSITIONAL_LONG_OPTIONS: dict[str, tuple[str, ...]] = {
    "run": ("--help",),
    "jobs": ("--help",),
    "log": ("--help", "--failed", "--max-bytes"),
    "checks": ("--help",),
    "artifacts": ("--help",),
}
VALUE_OPTIONS = ("--max-bytes",)
RUN_ID_LABEL = "run id"
RUNS_SOURCE = "`workflow_inspect.py runs`"
CONFIRM_RUN_ID_ACTION = f"confirm the run id with {RUNS_SOURCE}"


def _run(cmd: list[str]) -> tuple[int, str, str]:
    """Run one `gh` command; the single seam every subcommand reaches `gh` through.

    Returns (exit code, stdout verbatim, stderr stripped). Tests replace this
    function to supply recorded `gh` output without live credentials.
    """
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


def _error(subcommand: str, argument: str | None, cause: str, action: str) -> str:
    """Compose an error naming the subcommand and argument, the cause, and the next action."""
    target = subcommand if argument is None else f"{subcommand} {argument}"
    return f"{target}: {cause}. Next: {action}."


def _gh_failure(
    subcommand: str, argument: str | None, gh_name: str, code: int, detail: str
) -> str:
    if code == 124:
        action = "retry once; if it times out again, narrow the request or check network access"
    else:
        action = (
            "run python3 gh_access.py to check gh authentication and repository "
            "access, then retry"
        )
    cause = f"gh {gh_name} exited {code}: {detail or 'no output'}"
    return _error(subcommand, argument, cause, action)


def _validate_id(subcommand: str, label: str, value: str, source: str) -> str | None:
    if value.isascii() and value.isdigit() and int(value) > 0:
        return None
    return _error(
        subcommand,
        value,
        f"{label} must be a positive integer, got '{value}'",
        f"pass the number from {source}",
    )


def _is_option(token: str, long_options: tuple[str, ...]) -> bool:
    """Report whether argparse reads `token` as one of the subcommand's options."""
    if token == "-h":
        return True
    name = token.split("=", 1)[0]
    return (
        len(name) > 2
        and name.startswith("--")
        and any(option.startswith(name) for option in long_options)
    )


def _hoist_dash_led_positional(argv: list[str]) -> tuple[list[str], str | None]:
    """Detach a dash-led run id or pull request number from `argv`.

    argparse reads a token such as `--5` or `-abc` as an unknown option and
    exits 2 with a usage error. When the first token after the subcommand that
    is not one of its options (or an option's value) starts with a dash, return
    `argv` with a placeholder number in its place and the original token, so the
    positional validation reports it like any other non-positive-integer value.
    """
    if len(argv) < 3 or argv[1] not in POSITIONAL_LONG_OPTIONS:
        return argv, None
    long_options = POSITIONAL_LONG_OPTIONS[argv[1]]
    index = 2
    while index < len(argv):
        token = argv[index]
        if token == "--":
            return argv, None
        if _is_option(token, long_options):
            takes_value = "=" not in token and any(
                option.startswith(token) for option in VALUE_OPTIONS
            )
            index += 2 if takes_value else 1
            continue
        if token.startswith("-") and token != "-":
            hoisted = [*argv[:index], POSITIONAL_PLACEHOLDER, *argv[index + 1 :]]
            return hoisted, token
        return argv, None
    return argv, None


def _gh_json(
    subcommand: str, argument: str | None, gh_name: str, args: list[str]
) -> tuple[Any, str | None]:
    code, out, err = _run(args)
    if code != 0:
        return None, _gh_failure(
            subcommand, argument, gh_name, code, err or out.strip()
        )
    try:
        return json.loads(out), None
    except json.JSONDecodeError as exc:
        return None, _error(
            subcommand,
            argument,
            f"gh {gh_name} returned output that is not JSON ({exc})",
            "run python3 gh_access.py to check the gh version and authentication, then retry",
        )


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
    if limit < 1:
        return {
            "schema_version": SCHEMA_VERSION,
            "runs": [],
            "error": _error(
                "runs",
                f"--limit {limit}",
                "limit must be at least 1",
                "pass --limit with a positive integer",
            ),
        }
    data, err = _gh_json("runs", None, "run list", args)
    if err is not None or not isinstance(data, list):
        return {
            "schema_version": SCHEMA_VERSION,
            "runs": [],
            "error": err
            or _error(
                "runs",
                None,
                f"gh run list returned {type(data).__name__}, not a list",
                "run python3 gh_access.py to check the gh version and "
                "authentication, then rerun `workflow_inspect.py runs`",
            ),
        }
    return {"schema_version": SCHEMA_VERSION, "runs": data, "error": None}


def cmd_run(run_id: str) -> dict[str, Any]:
    fields = (
        "databaseId,status,conclusion,workflowName,headBranch,headSha,createdAt,jobs"
    )
    invalid = _validate_id("run", RUN_ID_LABEL, run_id, RUNS_SOURCE)
    if invalid:
        return {"schema_version": SCHEMA_VERSION, "error": invalid}
    data, err = _gh_json(
        "run", run_id, "run view", ["gh", "run", "view", run_id, "--json", fields]
    )
    if err is not None or not isinstance(data, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "error": err
            or _error(
                "run",
                run_id,
                "gh run view returned no run object",
                CONFIRM_RUN_ID_ACTION,
            ),
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
    invalid = _validate_id("jobs", RUN_ID_LABEL, run_id, RUNS_SOURCE)
    if invalid:
        return {"schema_version": SCHEMA_VERSION, "jobs": [], "error": invalid}
    data, err = _gh_json(
        "jobs", run_id, "run view", ["gh", "run", "view", run_id, "--json", "jobs"]
    )
    if err is not None or not isinstance(data, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "jobs": [],
            "error": err
            or _error(
                "jobs",
                run_id,
                "gh run view returned no jobs object",
                CONFIRM_RUN_ID_ACTION,
            ),
        }
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
    log_flag = "--log-failed" if failed else "--log"
    failure = {
        "schema_version": SCHEMA_VERSION,
        "log": "",
        "failed_only": failed,
        "byte_count": 0,
        "truncated": False,
    }
    invalid = _validate_id("log", RUN_ID_LABEL, run_id, RUNS_SOURCE)
    if invalid:
        return {**failure, "error": invalid}
    if max_bytes < 1:
        return {
            **failure,
            "error": _error(
                "log",
                f"--max-bytes {max_bytes}",
                "max-bytes must be at least 1",
                "pass --max-bytes with a positive integer",
            ),
        }
    code, out, err = _run(["gh", "run", "view", run_id, log_flag])
    if code != 0:
        return {
            **failure,
            "error": _gh_failure(
                "log", run_id, f"run view {log_flag}", code, err or out.strip()
            ),
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
    invalid = _validate_id(
        "checks", "pull request number", pr_number, "`gh pr list` or the PR URL"
    )
    if invalid:
        return {"schema_version": SCHEMA_VERSION, "error": invalid}
    data, err = _gh_json(
        "checks",
        pr_number,
        "pr view",
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--json",
            "number,headRefName,statusCheckRollup",
        ],
    )
    if err is not None or not isinstance(data, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "error": err
            or _error(
                "checks",
                pr_number,
                "gh pr view returned no pull request object",
                "confirm the pull request number",
            ),
        }
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
    invalid = _validate_id("artifacts", RUN_ID_LABEL, run_id, RUNS_SOURCE)
    if invalid:
        return {"schema_version": SCHEMA_VERSION, "artifacts": [], "error": invalid}
    data, err = _gh_json(
        "artifacts",
        run_id,
        "api",
        [
            "gh",
            "api",
            f"repos/:owner/:repo/actions/runs/{run_id}/artifacts",
            "--jq",
            "{artifacts: [.artifacts[] | {id, name, size_in_bytes, expired}]}",
        ],
    )
    if err is not None or not isinstance(data, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "artifacts": [],
            "error": err
            or _error(
                "artifacts",
                run_id,
                "gh api returned no artifacts object",
                CONFIRM_RUN_ID_ACTION,
            ),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifacts": data.get("artifacts", []),
        "error": None,
    }


def cmd_workflow_files() -> dict[str, Any]:
    data, err = _gh_json(
        "workflow-files",
        None,
        "workflow list",
        [
            "gh",
            "workflow",
            "list",
            "--json",
            "id,name,state,path",
        ],
    )
    if err is not None or not isinstance(data, list):
        return {
            "schema_version": SCHEMA_VERSION,
            "workflows": [],
            "error": err
            or _error(
                "workflow-files",
                None,
                "gh workflow list returned no list",
                "run python3 gh_access.py to check repository access",
            ),
        }
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

    parse_argv, dash_led = _hoist_dash_led_positional(argv)
    args = parser.parse_args(parse_argv[1:])
    if dash_led is not None:
        if args.cmd == "checks":
            args.pr_number = dash_led
        else:
            args.run_id = dash_led

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

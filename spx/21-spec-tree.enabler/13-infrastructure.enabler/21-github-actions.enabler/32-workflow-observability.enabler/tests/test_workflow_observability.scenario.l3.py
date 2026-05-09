"""Scenario tests for github-actions helpers that require gh credentials and a github.com remote."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[6]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "github-actions"
    / "scripts"
)
GH_ACCESS = SCRIPTS_DIR / "gh_access.py"
WORKFLOW_INSPECT = SCRIPTS_DIR / "workflow_inspect.py"


def require_gh_authenticated() -> None:
    proc = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.fail(
            "gh CLI must be authenticated for this test; run `gh auth login` and retry"
        )


def require_github_remote() -> None:
    proc = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True
    )
    if proc.returncode != 0 or "github.com" not in proc.stdout:
        pytest.fail(
            "origin remote must point at github.com for this test; got "
            f"{proc.stdout.strip()!r} (rc={proc.returncode})"
        )


def require_run_id() -> str:
    proc = subprocess.run(
        ["gh", "run", "list", "--limit", "1", "--json", "databaseId"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        pytest.fail(f"gh run list failed: {proc.stderr.strip()}")
    runs = json.loads(proc.stdout or "[]")
    if not runs:
        pytest.fail("at least one workflow run is required for this test")
    return str(runs[0]["databaseId"])


def test_gh_access_returns_documented_fields() -> None:
    """gh_access.py returns the documented JSON fields and respects stdin TTY redirection."""
    require_gh_authenticated()
    require_github_remote()
    proc = subprocess.run(
        [sys.executable, str(GH_ACCESS)],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    assert proc.returncode == 0, f"gh_access.py exited {proc.returncode}: {proc.stderr}"
    payload = json.loads(proc.stdout)
    for field in (
        "schema_version",
        "owner_repo",
        "host",
        "current_account",
        "has_access",
        "available_accounts",
        "is_tty",
        "error",
    ):
        assert field in payload, f"gh_access.py JSON missing field {field!r}"
    assert isinstance(payload["available_accounts"], list)
    assert isinstance(payload["has_access"], bool)
    assert isinstance(payload["is_tty"], bool)
    assert payload["is_tty"] is False, (
        "stdin redirected to DEVNULL must yield is_tty=False"
    )


def test_workflow_inspect_run_returns_documented_fields() -> None:
    """workflow_inspect.py `run <id>` returns the documented run + jobs JSON shape."""
    require_gh_authenticated()
    require_github_remote()
    run_id = require_run_id()
    proc = subprocess.run(
        [sys.executable, str(WORKFLOW_INSPECT), "run", run_id],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"workflow_inspect run exited {proc.returncode}: {proc.stderr}"
    )
    payload = json.loads(proc.stdout)
    for field in (
        "schema_version",
        "databaseId",
        "status",
        "conclusion",
        "workflowName",
        "headBranch",
        "headSha",
        "createdAt",
        "jobs",
    ):
        assert field in payload, f"workflow_inspect run output missing field {field!r}"
    assert isinstance(payload["jobs"], list)
    if payload["jobs"]:
        for job_field in ("databaseId", "name", "status", "conclusion"):
            assert job_field in payload["jobs"][0], (
                f"job entry missing field {job_field!r}"
            )

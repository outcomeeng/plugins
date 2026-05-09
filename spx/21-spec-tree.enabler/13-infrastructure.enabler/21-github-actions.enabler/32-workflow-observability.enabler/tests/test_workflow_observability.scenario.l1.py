"""Behavioral tests for github-actions helpers: gh_access, workflow_inspect, mutation_gate."""

from __future__ import annotations

import json
import os
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
MUTATION_GATE = SCRIPTS_DIR / "mutation_gate.py"


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


def test_mutation_gate_blocks_without_user_instructed(tmp_path: pathlib.Path) -> None:
    """mutation_gate.py `check <gated-cmd>` exits non-zero and writes a JSON error to stderr naming the missing consent flag."""
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    proc = subprocess.run(
        [
            sys.executable,
            str(MUTATION_GATE),
            "check",
            "gh",
            "auth",
            "switch",
            "-u",
            "test",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode != 0, (
        "gated mutation must exit non-zero without --user-instructed"
    )
    assert proc.stderr.strip(), "gated mutation must write JSON error to stderr"
    payload = json.loads(proc.stderr)
    assert payload["gated"] is True
    assert payload["missing_flag"] == "--user-instructed"
    assert payload["label"] == "gh auth switch"
    assert "gh auth switch" in payload["command"]


def test_mutation_gate_passes_with_user_instructed(tmp_path: pathlib.Path) -> None:
    """mutation_gate.py `check --user-instructed <gated-cmd>` exits zero and appends one tab-separated line (timestamp, account, label, command) to the audit log."""
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    proc = subprocess.run(
        [
            sys.executable,
            str(MUTATION_GATE),
            "check",
            "--user-instructed",
            "gh",
            "auth",
            "switch",
            "-u",
            "test",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, (
        f"explicit user-instructed call must exit zero: {proc.stderr}"
    )
    payload = json.loads(proc.stdout)
    assert payload["gated"] is True
    assert payload["label"] == "gh auth switch"
    audit_path = tmp_path / ".spx" / "mutation-audit.log"
    assert audit_path.exists(), "audit log file must be created"
    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, f"expected one audit line, got {len(lines)}"
    fields = lines[0].split("\t")
    assert len(fields) == 4, (
        f"audit line must have 4 tab-separated fields: {lines[0]!r}"
    )
    timestamp, _account, label, command = fields
    assert label == "gh auth switch"
    assert "gh auth switch" in command
    assert timestamp.endswith("Z"), f"timestamp must be UTC ISO-8601: {timestamp!r}"

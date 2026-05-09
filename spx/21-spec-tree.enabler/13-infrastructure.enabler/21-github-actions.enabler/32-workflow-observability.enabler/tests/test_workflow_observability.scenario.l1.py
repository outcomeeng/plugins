"""Behavioral tests for github-actions helpers that don't require gh credentials."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[6]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "github-actions"
    / "scripts"
)
MUTATION_GATE = SCRIPTS_DIR / "mutation_gate.py"

EXPECTED_AUDIT_FIELD_COUNT = 4


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
    """mutation_gate.py `check --user-instructed <gated-cmd>` exits zero and appends one tab-separated line (timestamp, account, label, command) to the audit log.

    `account` is whatever `gh api user` returns at run time, falling back to the literal "unknown"
    when gh is unauthenticated; the test asserts the field is present, not that it names a real
    account.
    """
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
    assert len(fields) == EXPECTED_AUDIT_FIELD_COUNT, (
        f"audit line must have {EXPECTED_AUDIT_FIELD_COUNT} tab-separated fields: {lines[0]!r}"
    )
    timestamp, _account, label, command = fields
    assert label == "gh auth switch"
    assert "gh auth switch" in command
    assert timestamp.endswith("Z"), f"timestamp must be UTC ISO-8601: {timestamp!r}"

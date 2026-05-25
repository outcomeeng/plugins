"""Property tests for github-actions helpers."""

from __future__ import annotations

import ast
import json
import os
import pathlib
import subprocess
import sys

import pytest

# parents[6] = repo root (this file lives 6 levels deep: spx/21-spec-tree/
# 13-infrastructure/21-github-actions/32-workflow-observability/tests/<file>).
# Tree surgery that changes the enabler's depth must update this index.
SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[6]
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "github-actions"
    / "scripts"
)

HELPERS = (
    SCRIPTS_DIR / "gh_access.py",
    SCRIPTS_DIR / "workflow_inspect.py",
    SCRIPTS_DIR / "mutation_gate.py",
)

# Modules accepted as "Python stdlib only" per the property assertion.
ALLOWED_STDLIB_MODULES = frozenset(
    {
        "__future__",
        "argparse",
        "datetime",
        "json",
        "os",
        "pathlib",
        "re",
        "subprocess",
        "sys",
        "typing",
    }
)


def _top_level_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".", 1)[0])
    return imports


@pytest.mark.parametrize("helper", HELPERS, ids=lambda p: p.name)
def test_helper_uses_only_stdlib_imports(helper: pathlib.Path) -> None:
    """Each helper imports only Python stdlib modules — no third-party HTTP libraries, no streaming subprocess wrappers."""
    source = helper.read_text(encoding="utf-8")
    imports = _top_level_imports(source)
    extra = imports - ALLOWED_STDLIB_MODULES
    assert not extra, f"{helper.name} imports non-stdlib modules: {sorted(extra)}"


def test_mutation_gate_emits_schema_version_in_stdout_json(
    tmp_path: pathlib.Path,
) -> None:
    """Helper stdout JSON includes a schema_version field (verified via mutation_gate passthrough — no network needed)."""
    mutation_gate = SCRIPTS_DIR / "mutation_gate.py"
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    proc = subprocess.run(
        [sys.executable, str(mutation_gate), "check", "echo", "hello"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "schema_version" in payload
    assert isinstance(payload["schema_version"], int)
    assert payload["schema_version"] == 1


def test_gh_access_emits_schema_version_in_stdout_json() -> None:
    """gh_access.py always emits schema_version on stdout, even when the repository is non-GitHub or gh is unauthenticated."""
    gh_access = SCRIPTS_DIR / "gh_access.py"
    proc = subprocess.run(
        [sys.executable, str(gh_access), "nonexistent-owner-xyz/nonexistent-repo-xyz"],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    # Exit code may be 0 or 1 depending on access; stdout must always be valid JSON with schema_version.
    payload = json.loads(proc.stdout)
    assert "schema_version" in payload
    assert payload["schema_version"] == 1


def test_mutation_gate_diagnostics_separate_stdout_stderr(
    tmp_path: pathlib.Path,
) -> None:
    """When exit zero, helper JSON goes to stdout and diagnostic output goes to stderr."""
    mutation_gate = SCRIPTS_DIR / "mutation_gate.py"
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    proc = subprocess.run(
        [sys.executable, str(mutation_gate), "check", "echo", "hello"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0
    json.loads(proc.stdout)  # parses cleanly
    assert proc.stderr == "", (
        f"passthrough should not write to stderr; got: {proc.stderr!r}"
    )


def test_mutation_gate_blocked_command_writes_only_to_stderr(
    tmp_path: pathlib.Path,
) -> None:
    """When a gated command is blocked, JSON error goes to stderr and stdout stays empty."""
    mutation_gate = SCRIPTS_DIR / "mutation_gate.py"
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    proc = subprocess.run(
        [
            sys.executable,
            str(mutation_gate),
            "check",
            "gh",
            "auth",
            "switch",
            "-u",
            "x",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode != 0
    assert proc.stdout == "", (
        f"blocked gate must keep stdout empty; got: {proc.stdout!r}"
    )
    payload = json.loads(proc.stderr)
    assert payload["gated"] is True
    assert payload["missing_flag"] == "--user-instructed"

"""Behavioral tests for github-actions helpers that don't require gh credentials."""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from types import ModuleType

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
    / "inspect-github-actions"
    / "scripts"
)
MUTATION_GATE = SCRIPTS_DIR / "mutation_gate.py"
GH_ACCESS = SCRIPTS_DIR / "gh_access.py"

EXPECTED_AUDIT_FIELD_COUNT = 4


def _load_gh_access_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gh_access_under_test", GH_ACCESS)
    assert spec is not None and spec.loader is not None, (
        f"could not build module spec for {GH_ACCESS}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_gh_access_parse_remote_returns_none_for_malformed_url() -> None:
    """parse_remote() returns None for inputs that match neither SCP nor URL form."""
    gh_access = _load_gh_access_module()
    assert gh_access.parse_remote("not-a-url") is None
    assert gh_access.parse_remote("") is None
    assert gh_access.parse_remote("github.com") is None


def test_gh_access_parse_remote_recognizes_scp_and_url_forms() -> None:
    """parse_remote() returns (host, owner/repo) for both SCP and URL remotes."""
    gh_access = _load_gh_access_module()
    assert gh_access.parse_remote("git@github.com:foo/bar.git") == (
        "github.com",
        "foo/bar",
    )
    assert gh_access.parse_remote("https://github.com/foo/bar.git") == (
        "github.com",
        "foo/bar",
    )


def test_gh_access_uses_detected_host_for_enterprise_api_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gh_access = _load_gh_access_module()
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        calls.append(cmd)
        if cmd == ["git", "remote", "get-url", "origin"]:
            return 0, "git@github.example.com:foo/bar.git", ""
        if cmd[:3] == ["gh", "api", "repos/foo/bar"]:
            return 0, "bar", ""
        if cmd[:3] == ["gh", "api", "user"]:
            return 0, "octocat", ""
        if cmd == ["gh", "auth", "status", "--json", "hosts"]:
            return 0, '{"hosts": {}}', ""
        return 1, "", "unexpected command"

    monkeypatch.setattr(gh_access, "_run", fake_run)

    assert gh_access.main(["gh_access.py"]) == 0
    assert [
        "gh",
        "api",
        "repos/foo/bar",
        "--jq",
        ".name",
        "--hostname",
        "github.example.com",
    ] in calls
    assert [
        "gh",
        "api",
        "user",
        "--jq",
        ".login",
        "--hostname",
        "github.example.com",
    ] in calls


def test_gh_access_filters_available_accounts_to_detected_host(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    gh_access = _load_gh_access_module()

    def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        if cmd == ["git", "remote", "get-url", "origin"]:
            return 0, "git@github.example.com:foo/bar.git", ""
        if cmd[:3] == ["gh", "api", "repos/foo/bar"]:
            return 1, "", "not found"
        if cmd[:3] == ["gh", "api", "user"]:
            return 0, "octocat", ""
        if cmd == ["gh", "auth", "status", "--json", "hosts"]:
            return (
                0,
                json.dumps(
                    {
                        "hosts": {
                            "github.com": [{"login": "public-account"}],
                            "github.example.com": [{"login": "enterprise-account"}],
                        }
                    }
                ),
                "",
            )
        return 1, "", "unexpected command"

    monkeypatch.setattr(gh_access, "_run", fake_run)

    assert gh_access.main(["gh_access.py"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["available_accounts"] == ["enterprise-account"]


def test_gh_access_emits_owner_repo_null_when_outside_git_repo(
    tmp_path: pathlib.Path,
) -> None:
    """Running gh_access.py outside a git checkout (no `origin` remote) yields owner_repo=null."""
    proc = subprocess.run(
        [sys.executable, str(GH_ACCESS)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
    )
    payload = json.loads(proc.stdout)
    assert payload["owner_repo"] is None
    assert payload["host"] is None
    assert payload["schema_version"] == 1

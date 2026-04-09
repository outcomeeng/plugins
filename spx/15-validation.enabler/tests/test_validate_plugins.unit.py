"""Unit tests for plugin manifest validation.

Tests the validate-plugins.py script against the assertions
in spx/15-validation.enabler/validation.md (Plugin Manifest Validation).

Level 1: discovery logic is pure path computation.
Subprocess execution of `claude plugin validate` is thin glue tested at
Level 2 by the pre-commit hook itself.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from outcomeeng.scripts.validate_plugins import discover_targets, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_marketplace(tmp_path: Path) -> Path:
    """Create a directory with .claude-plugin/marketplace.json."""
    manifest_dir = tmp_path / ".claude-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "marketplace.json").write_text('{"plugins": []}')
    return tmp_path


def _make_plugin(tmp_path: Path, name: str) -> Path:
    """Create a plugin directory under tmp_path/plugins/<name>/."""
    plugin_dir = tmp_path / "plugins" / name
    manifest_dir = plugin_dir / ".claude-plugin"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "plugin.json").write_text(
        f'{{"name": "{name}", "version": "0.1.0"}}'
    )
    return plugin_dir


# ---------------------------------------------------------------------------
# Scenario: marketplace discovered and validated
# ---------------------------------------------------------------------------


def test_discovers_marketplace(tmp_path: Path) -> None:
    _make_marketplace(tmp_path)
    targets = discover_targets(tmp_path)
    assert tmp_path in targets


# ---------------------------------------------------------------------------
# Scenario: plugin directories discovered and validated
# ---------------------------------------------------------------------------


def test_discovers_plugins(tmp_path: Path) -> None:
    _make_marketplace(tmp_path)
    plugin_a = _make_plugin(tmp_path, "alpha")
    plugin_b = _make_plugin(tmp_path, "beta")
    targets = discover_targets(tmp_path)
    assert plugin_a in targets
    assert plugin_b in targets


# ---------------------------------------------------------------------------
# Scenario: failed validation exits non-zero and reports which plugin failed
# ---------------------------------------------------------------------------


def test_failed_validation_exits_nonzero_and_reports(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_marketplace(tmp_path)
    _make_plugin(tmp_path, "bad-plugin")

    def fake_runner(
        cmd: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        target = cmd[-1]
        if "bad-plugin" in target:
            return subprocess.CompletedProcess(
                cmd, returncode=1, stdout="", stderr="validation failed"
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    exit_code = main([str(tmp_path)], runner=fake_runner)

    assert exit_code != 0
    captured = capsys.readouterr()
    assert "bad-plugin" in captured.err


# ---------------------------------------------------------------------------
# Scenario: no marketplace or plugins found exits non-zero
# ---------------------------------------------------------------------------


def test_no_targets_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(tmp_path)])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert captured.err  # some error message printed

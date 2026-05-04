"""Level 1 scenario tests for plugin manifest validation.

Tests the validate-plugins.py script against the assertions
in [plugin-manifest.md](../plugin-manifest.md).

Level 1: discovery logic is pure path computation.
Subprocess execution of `claude plugin validate` is thin glue tested at
Level 2 by the pre-commit hook itself.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from outcomeeng.scripts.validate_plugins import (
    check_catalog_sync,
    check_manifest_parity,
    discover_targets,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_claude_catalog(tmp_path: Path, registered: list[str] | None = None) -> Path:
    """Create .claude-plugin/marketplace.json listing the given plugin names."""
    manifest_dir = tmp_path / ".claude-plugin"
    manifest_dir.mkdir(exist_ok=True)
    plugins = [{"name": n} for n in (registered or [])]
    (manifest_dir / "marketplace.json").write_text(json.dumps({"plugins": plugins}))
    return tmp_path


def _make_codex_catalog(tmp_path: Path, registered: list[str] | None = None) -> Path:
    """Create .agents/plugins/marketplace.json listing the given plugin names."""
    catalog_dir = tmp_path / ".agents" / "plugins"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    plugins = [{"name": n} for n in (registered or [])]
    (catalog_dir / "marketplace.json").write_text(json.dumps({"plugins": plugins}))
    return tmp_path


def _make_marketplace(tmp_path: Path) -> Path:
    """Create both marketplace catalogs with no registered plugins."""
    _make_claude_catalog(tmp_path)
    _make_codex_catalog(tmp_path)
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


def _add_codex_manifest(plugin_dir: Path, version: str | None) -> Path:
    """Add a .codex-plugin/plugin.json to an existing plugin dir.

    When ``version`` is None, the file is written without a version field
    so the parity check can exercise the missing-field branch.
    """
    codex_dir = plugin_dir / ".codex-plugin"
    codex_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, str] = {"name": plugin_dir.name}
    if version is not None:
        payload["version"] = version
    (codex_dir / "plugin.json").write_text(json.dumps(payload))
    return codex_dir / "plugin.json"


def _set_claude_version(plugin_dir: Path, version: str | None) -> None:
    """Rewrite an existing .claude-plugin/plugin.json with a chosen version.

    When ``version`` is None, the file is written without a version field
    so the parity check can exercise the missing-field branch.
    """
    payload: dict[str, str] = {"name": plugin_dir.name}
    if version is not None:
        payload["version"] = version
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(json.dumps(payload))


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
    _make_claude_catalog(tmp_path, registered=["bad-plugin"])
    _make_codex_catalog(tmp_path, registered=["bad-plugin"])
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


# ---------------------------------------------------------------------------
# Scenario: catalog sync — plugin directory not registered in a catalog
# ---------------------------------------------------------------------------


def test_sync_plugin_missing_from_claude_catalog(tmp_path: Path) -> None:
    _make_plugin(tmp_path, "alpha")
    _make_claude_catalog(tmp_path, registered=[])  # exists but alpha not listed
    _make_codex_catalog(tmp_path, registered=["alpha"])

    errors = check_catalog_sync(tmp_path)

    assert any("claude" in e and "alpha" in e for e in errors)


def test_sync_plugin_missing_from_codex_catalog(tmp_path: Path) -> None:
    _make_plugin(tmp_path, "alpha")
    _make_claude_catalog(tmp_path, registered=["alpha"])
    _make_codex_catalog(tmp_path, registered=[])  # exists but alpha not listed

    errors = check_catalog_sync(tmp_path)

    assert any("codex" in e and "alpha" in e for e in errors)


def test_sync_returns_no_errors_when_both_catalogs_match(tmp_path: Path) -> None:
    _make_plugin(tmp_path, "alpha")
    _make_plugin(tmp_path, "beta")
    _make_claude_catalog(tmp_path, registered=["alpha", "beta"])
    _make_codex_catalog(tmp_path, registered=["alpha", "beta"])

    errors = check_catalog_sync(tmp_path)

    assert errors == []


def test_sync_reports_catalog_entry_without_plugin_directory(tmp_path: Path) -> None:
    _make_claude_catalog(tmp_path, registered=["ghost"])
    _make_codex_catalog(tmp_path, registered=["ghost"])
    # No plugins/ghost/ directory

    errors = check_catalog_sync(tmp_path)

    assert any("ghost" in e for e in errors)


def test_sync_main_exits_nonzero_on_catalog_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _make_claude_catalog(tmp_path, registered=[])
    _make_codex_catalog(tmp_path, registered=[])
    _make_plugin(tmp_path, "unregistered")

    def fake_runner(
        cmd: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    exit_code = main([str(tmp_path)], runner=fake_runner)

    assert exit_code != 0
    captured = capsys.readouterr()
    assert "unregistered" in captured.err


# ---------------------------------------------------------------------------
# Scenario: manifest parity — versions match across both manifests
# ---------------------------------------------------------------------------


def test_parity_passes_when_both_manifests_agree(tmp_path: Path) -> None:
    plugin = _make_plugin(tmp_path, "alpha")
    _set_claude_version(plugin, "0.27.3")
    _add_codex_manifest(plugin, "0.27.3")

    errors = check_manifest_parity(tmp_path)

    assert errors == []


# ---------------------------------------------------------------------------
# Scenario: manifest parity — version mismatch reported with both versions
# ---------------------------------------------------------------------------


def test_parity_reports_version_drift_with_both_versions(tmp_path: Path) -> None:
    plugin = _make_plugin(tmp_path, "alpha")
    _set_claude_version(plugin, "0.27.3")
    _add_codex_manifest(plugin, "0.27.0")

    errors = check_manifest_parity(tmp_path)

    assert len(errors) == 1
    error = errors[0]
    assert "alpha" in error
    assert "0.27.3" in error
    assert "0.27.0" in error
    assert "drift" in error.lower()


# ---------------------------------------------------------------------------
# Scenario: manifest parity — Codex manifest absent, parity check skipped
# ---------------------------------------------------------------------------


def test_parity_skipped_when_codex_manifest_absent(tmp_path: Path) -> None:
    _make_plugin(tmp_path, "alpha")  # only .claude-plugin/plugin.json
    # No _add_codex_manifest call — Codex coverage is optional.

    errors = check_manifest_parity(tmp_path)

    assert errors == []


# ---------------------------------------------------------------------------
# Scenario: manifest parity — missing version field reported
# ---------------------------------------------------------------------------


def test_parity_reports_missing_claude_version(tmp_path: Path) -> None:
    plugin = _make_plugin(tmp_path, "alpha")
    _set_claude_version(plugin, None)
    _add_codex_manifest(plugin, "0.27.0")

    errors = check_manifest_parity(tmp_path)

    assert any("alpha" in e and "claude-plugin" in e and "missing" in e for e in errors)


def test_parity_reports_missing_codex_version(tmp_path: Path) -> None:
    plugin = _make_plugin(tmp_path, "alpha")
    _set_claude_version(plugin, "0.27.3")
    _add_codex_manifest(plugin, None)

    errors = check_manifest_parity(tmp_path)

    assert any("alpha" in e and "codex-plugin" in e and "missing" in e for e in errors)


# ---------------------------------------------------------------------------
# Property: parity is symmetric — drift in either direction is reported
# ---------------------------------------------------------------------------


def test_parity_drift_reported_when_codex_advanced_past_claude(tmp_path: Path) -> None:
    plugin = _make_plugin(tmp_path, "alpha")
    _set_claude_version(plugin, "0.27.0")
    _add_codex_manifest(plugin, "0.27.3")

    errors = check_manifest_parity(tmp_path)

    assert len(errors) == 1
    assert "alpha" in errors[0]


def test_parity_drift_reported_when_claude_advanced_past_codex(tmp_path: Path) -> None:
    plugin = _make_plugin(tmp_path, "alpha")
    _set_claude_version(plugin, "0.27.3")
    _add_codex_manifest(plugin, "0.27.0")

    errors = check_manifest_parity(tmp_path)

    assert len(errors) == 1
    assert "alpha" in errors[0]


# ---------------------------------------------------------------------------
# Compliance: main() exits non-zero when parity drift exists
# ---------------------------------------------------------------------------


def test_main_exits_nonzero_on_parity_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plugin = _make_plugin(tmp_path, "alpha")
    _set_claude_version(plugin, "0.27.3")
    _add_codex_manifest(plugin, "0.27.0")
    _make_claude_catalog(tmp_path, registered=["alpha"])
    _make_codex_catalog(tmp_path, registered=["alpha"])

    def fake_runner(
        cmd: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    exit_code = main([str(tmp_path)], runner=fake_runner)

    assert exit_code != 0
    captured = capsys.readouterr()
    assert "alpha" in captured.err
    assert "manifest parity" in captured.err

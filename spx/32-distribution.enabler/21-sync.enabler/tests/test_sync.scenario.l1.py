"""Level-1 scenario evidence for `spx/32-distribution.enabler/21-sync.enabler/`.

Covers the scenario assertions in `sync.md`:
- No-change short-circuit: a non-empty `base_ref` with no plugin distribution
  diff exits 0 without invoking marketplace mutations.
- Change-driven sequence: a non-empty `base_ref` with a plugin distribution
  diff invokes the orchestration steps in order.
- Working-tree comparison: a non-empty `base_ref` with uncommitted distribution
  changes invokes the orchestration steps in order.

Runner exit codes, step calls, and tool-availability checks are observed
through the recording doubles in `outcomeeng_testing.harnesses.sync`.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

import outcomeeng.distribution.sync as sync_module
from outcomeeng.distribution.sync import (
    REQUIRED_TOOLS,
    STEPS,
    _worktree_path_for_branch,
    sync,
)
from outcomeeng_testing.harnesses.sync import (
    RecordingRunner,
    ScriptedChangeProbe,
    ScriptedConfigRepairer,
    ScriptedToolProbe,
)

ALL_TOOLS_AVAILABLE = frozenset(REQUIRED_TOOLS)
STEP_ARGVS: tuple[tuple[str, ...], ...] = tuple(step.argv for step in STEPS)


def test_default_branch_worktree_is_selected_from_porcelain_listing() -> None:
    listing = "\n".join(
        [
            "worktree /repo/plugins",
            "HEAD 1111111111111111111111111111111111111111",
            "branch refs/heads/main",
            "",
            "worktree /repo/plugins-d",
            "HEAD 2222222222222222222222222222222222222222",
            "branch refs/heads/work/manage-runtime-marketplaces",
            "",
        ],
    )

    assert _worktree_path_for_branch(listing, "main") == pathlib.Path(
        "/repo/plugins",
    )


def test_real_source_root_selects_default_branch_worktree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listing = "\n".join(
        [
            "worktree /repo/plugins",
            "HEAD 1111111111111111111111111111111111111111",
            "branch refs/heads/main",
            "",
            "worktree /repo/plugins-d",
            "HEAD 2222222222222222222222222222222222222222",
            "branch refs/heads/work/manage-runtime-marketplaces",
            "",
        ],
    )
    feature_root = pathlib.Path("/repo/plugins-d")

    monkeypatch.setattr(sync_module, "_real_default_branch_name", lambda: "main")
    monkeypatch.setattr(
        sync_module,
        "_real_worktree_root_for_branch",
        lambda branch: _worktree_path_for_branch(listing, branch),
    )
    monkeypatch.setattr(sync_module, "_real_git_toplevel", lambda: feature_root)

    assert sync_module._real_source_root() == pathlib.Path("/repo/plugins")


def test_default_branch_worktree_selection_ignores_detached_worktrees() -> None:
    listing = "\n".join(
        [
            "worktree /repo/plugins-d",
            "HEAD 2222222222222222222222222222222222222222",
            "detached",
            "",
        ],
    )

    assert _worktree_path_for_branch(listing, "main") is None


def test_no_distribution_changes_exits_zero_after_config_reconciliation() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 0
    assert runner.calls == []
    assert config_repairer.calls == 1
    assert change_probe.queries == ["abc123"]


def test_config_repair_runs_refresh_without_distribution_changes() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=True)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert change_probe.queries == ["abc123"]
    assert runner.calls == list(STEP_ARGVS)


def test_distribution_changes_invoke_all_steps_in_declared_order() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=True)
    config_repairer = ScriptedConfigRepairer(changed=False)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert runner.calls == list(STEP_ARGVS)


def test_sync_declares_codex_local_refresh_step() -> None:
    step_names = tuple(step.name for step in STEPS)

    assert "codex_local_refresh" in step_names
    assert "codex_cache_preserve" not in step_names


def test_absent_base_ref_runs_all_steps_without_consulting_change_probe() -> None:
    """When no base_ref is supplied there is no diff baseline; sync proceeds."""
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)

    exit_code = sync(
        None,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert runner.calls == list(STEP_ARGVS)
    assert change_probe.queries == []


@pytest.mark.parametrize("base_ref", ["", None])
def test_empty_base_ref_treated_as_no_baseline(base_ref: str | None) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)

    exit_code = sync(
        base_ref,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert runner.calls == list(STEP_ARGVS)
    assert change_probe.queries == []


def test_sync_detects_uncommitted_distribution_changes(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sync compares the base ref to the working tree through its public API."""
    _git(tmp_path, "init", "--initial-branch", "main", "--quiet")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("seed\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "seed", "--quiet")
    base_ref = _git(tmp_path, "rev-parse", "HEAD").strip()

    changed_manifest = tmp_path / "src/plugins/foo/.claude-plugin/plugin.json"
    changed_manifest.parent.mkdir(parents=True)
    changed_manifest.write_text('{"name": "foo", "version": "0.1.0"}\n')

    monkeypatch.chdir(tmp_path)
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    config_repairer = ScriptedConfigRepairer(changed=False)

    exit_code = sync(
        base_ref,
        runner=runner,
        tool_probe=tool_probe,
        config_repairer=config_repairer,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert runner.calls == list(STEP_ARGVS)


def _git(repo: pathlib.Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

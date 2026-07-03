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

from collections.abc import Sequence
import pathlib
import subprocess

import pytest

from outcomeeng.distribution.agents import install_agents
import outcomeeng.distribution.sync as sync_module
from outcomeeng.distribution.sync import (
    DISTRIBUTION_PATHS,
    REQUIRED_TOOLS,
    STEPS,
    _real_change_probe,
    _worktree_path_for_branch,
    sync,
)
from outcomeeng_testing.harnesses.sync import (
    RecordingRunner,
    ScriptedChangeProbe,
    ScriptedConfigRepairer,
    ScriptedToolProbe,
)
from outcomeeng_testing.harnesses.src_tree import write_agent_tree

ALL_TOOLS_AVAILABLE = frozenset(REQUIRED_TOOLS)
STEP_ARGVS: tuple[tuple[str, ...], ...] = tuple(step.argv for step in STEPS)
CODEX_FINAL_REFRESH_STEP = "codex_local_refresh_final"
INSTALL_VALIDATE_STEP_NAME = "install_validate"
INSTALLED_CHECK_STEP = "installed_check"
PLUGIN_NAME = "sample"
AGENT_NAME = "guarded-writer"
AGENT_INSTALL_MODULE = "outcomeeng.distribution.agents"
AGENT_INSTALL_STEP = next(step for step in STEPS if AGENT_INSTALL_MODULE in step.argv)
INSTALL_VALIDATE_STEP = next(
    step for step in STEPS if step.name == INSTALL_VALIDATE_STEP_NAME
)
SOURCE_AGENT = f"""---
name: {AGENT_NAME}
description: Guarded writer.
tools:
  - Read
---

Review write behavior.
"""


class AgentInstallRunner:
    """Runs only the generated-agent install step against a temp target."""

    def __init__(self, source_root: pathlib.Path, target_root: pathlib.Path) -> None:
        self.source_root = source_root
        self.target_root = target_root
        self.calls: list[tuple[str, ...]] = []
        self.agent_present_before_validation = False

    def __call__(self, argv: Sequence[str]) -> int:
        call = tuple(argv)
        self.calls.append(call)
        if call == AGENT_INSTALL_STEP.argv:
            install_agents(self.source_root, self.target_root)
        if call == INSTALL_VALIDATE_STEP.argv:
            self.agent_present_before_validation = bool(
                tuple(self.target_root.glob("*.toml"))
            )
        return 0


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


def test_sync_installs_codex_agents_before_installed_plugin_validation(
    tmp_path: pathlib.Path,
) -> None:
    source_root = write_agent_tree(tmp_path, PLUGIN_NAME, {AGENT_NAME: SOURCE_AGENT})
    target_root = tmp_path / "codex-agents"
    runner = AgentInstallRunner(source_root, target_root)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE),
        change_probe=ScriptedChangeProbe(changed=True),
        config_repairer=ScriptedConfigRepairer(changed=False),
    )

    call_indexes = {argv: index for index, argv in enumerate(runner.calls)}
    installed_agents = tuple(target_root.glob("*.toml"))

    assert exit_code == 0
    assert installed_agents
    assert runner.agent_present_before_validation
    assert (
        call_indexes[AGENT_INSTALL_STEP.argv] < call_indexes[INSTALL_VALIDATE_STEP.argv]
    )


def test_sync_runs_final_codex_refresh_after_install_validation() -> None:
    """Codex CLI reads during install validation and installed-skill checks can
    rewrite the cache from stale runtime state; the final refresh reconciles that
    drift after both read phases.
    """
    step_names = tuple(step.name for step in STEPS)

    assert CODEX_FINAL_REFRESH_STEP in step_names
    assert step_names.index(INSTALL_VALIDATE_STEP_NAME) < step_names.index(
        CODEX_FINAL_REFRESH_STEP
    )
    assert step_names.index(INSTALLED_CHECK_STEP) < step_names.index(
        CODEX_FINAL_REFRESH_STEP
    )
    assert (
        "--strict-current-cache"
        in STEPS[step_names.index(CODEX_FINAL_REFRESH_STEP)].argv
    )


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


@pytest.mark.parametrize("path_root", DISTRIBUTION_PATHS)
@pytest.mark.parametrize("tracked", [True, False])
def test_real_change_probe_detects_uncommitted_distribution_changes(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    path_root: str,
    tracked: bool,
) -> None:
    _git(tmp_path, "init", "--initial-branch", "main", "--quiet")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    changed_file = tmp_path / path_root / "distribution-probe.txt"
    if tracked:
        changed_file.parent.mkdir(parents=True)
        changed_file.write_text("initial\n", encoding="utf-8")
        _git(tmp_path, "add", path_root)
    else:
        (tmp_path / "README.md").write_text("seed\n", encoding="utf-8")
        _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "seed", "--quiet")
    base_ref = _git(tmp_path, "rev-parse", "HEAD").strip()

    changed_file.parent.mkdir(parents=True, exist_ok=True)
    changed_file.write_text("changed\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    assert _real_change_probe(base_ref)


def _git(repo: pathlib.Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

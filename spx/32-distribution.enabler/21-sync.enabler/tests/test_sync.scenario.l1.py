"""Level-1 scenario evidence for `spx/32-distribution.enabler/21-sync.enabler/`.

Covers the two scenario assertions in `sync.md`:
- No-change short-circuit: a non-empty `base_ref` with no plugin distribution
  diff exits 0 without invoking marketplace mutations.
- Change-driven sequence: a non-empty `base_ref` with a plugin distribution
  diff invokes the orchestration steps in order.

Runner exit codes, step calls, and tool-availability checks are observed
through the recording doubles in `outcomeeng_testing.harnesses.sync`.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

from outcomeeng.distribution.sync import REQUIRED_TOOLS, STEPS, _real_change_probe, sync
from outcomeeng_testing.harnesses.sync import (
    RecordingRunner,
    ScriptedChangeProbe,
    ScriptedToolProbe,
)

ALL_TOOLS_AVAILABLE = frozenset(REQUIRED_TOOLS)
STEP_ARGVS: tuple[tuple[str, ...], ...] = tuple(step.argv for step in STEPS)


def test_no_distribution_changes_exits_zero_without_running_steps() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
    )

    assert exit_code == 0
    assert runner.calls == []
    assert change_probe.queries == ["abc123"]


def test_distribution_changes_invoke_all_steps_in_declared_order() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=True)

    exit_code = sync(
        "abc123",
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
    )

    assert exit_code == 0
    assert runner.calls == list(STEP_ARGVS)


def test_absent_base_ref_runs_all_steps_without_consulting_change_probe() -> None:
    """When no base_ref is supplied there is no diff baseline; sync proceeds."""
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)

    exit_code = sync(
        None,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
    )

    assert exit_code == 0
    assert runner.calls == list(STEP_ARGVS)
    assert change_probe.queries == []


@pytest.mark.parametrize("base_ref", ["", None])
def test_empty_base_ref_treated_as_no_baseline(base_ref: str | None) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)

    exit_code = sync(
        base_ref,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
    )

    assert exit_code == 0
    assert runner.calls == list(STEP_ARGVS)
    assert change_probe.queries == []


def test_real_change_probe_detects_uncommitted_distribution_changes(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real adapter compares the base ref to the working tree so a local
    marketplace sync before commit still runs when `src/` or `dist/` changed.
    """
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

    assert _real_change_probe(base_ref) is True


def _git(repo: pathlib.Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

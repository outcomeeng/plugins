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
import os
import pathlib
import subprocess
import sys

import pytest

import outcomeeng.distribution.sync as sync_module
from outcomeeng.distribution.codex_cache import InstalledSetError
from outcomeeng.distribution.sync import (
    DISTRIBUTION_PATHS,
    REQUIRED_TOOLS,
    STEPS,
    _real_change_probe,
    _FileSingleFlight,
    _worktree_path_for_branch,
    sync,
)
from outcomeeng_testing.harnesses.sync import (
    DEFAULT_TOPOLOGY_ERRORS,
    RecordingRunner,
    SCRIPTED_BASE_REF,
    ScriptedChangeProbe,
    ScriptedConfigRepairer,
    ScriptedSingleFlight,
    ScriptedToolProbe,
    ScriptedTopologyProbe,
    run_invalid_topology_refresh,
)

ALL_TOOLS_AVAILABLE = frozenset(REQUIRED_TOOLS)
STEP_ARGVS: tuple[tuple[str, ...], ...] = tuple(step.argv for step in STEPS)
CODEX_FINAL_REFRESH_STEP = "codex_local_refresh_final"
INSTALL_VALIDATE_STEP_NAME = "install_validate"
INSTALLED_CHECK_STEP = "installed_check"
PLUGIN_NAME = "sample"
AGENT_NAME = "guarded-writer"
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


def test_default_branch_worktree_preserves_slash_containing_branch() -> None:
    listing = "\n".join(
        [
            "worktree /repo/plugins",
            "HEAD 1111111111111111111111111111111111111111",
            "branch refs/heads/release/main",
            "",
            "worktree /repo/plugins-d",
            "HEAD 2222222222222222222222222222222222222222",
            "branch refs/heads/main",
            "",
        ],
    )

    assert _worktree_path_for_branch(listing, "release/main") == pathlib.Path(
        "/repo/plugins",
    )


def test_real_source_root_selects_default_branch_worktree(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "plugins"
    feature_root = tmp_path / "plugins-d"
    repo_root.mkdir()
    _git(repo_root, "init", "--initial-branch", "main", "--quiet")
    _git(repo_root, "config", "user.email", "test@example.invalid")
    _git(repo_root, "config", "user.name", "Test")
    (repo_root / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo_root, "add", "README.md")
    _git(repo_root, "commit", "-m", "seed", "--quiet")
    _git(repo_root, "branch", "work/manage-runtime-marketplaces")
    _git(
        repo_root,
        "worktree",
        "add",
        "--quiet",
        str(feature_root),
        "work/manage-runtime-marketplaces",
    )

    monkeypatch.chdir(feature_root)

    assert sync_module._real_source_root() == repo_root


def test_real_source_root_preserves_slash_containing_default_branch(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "plugins"
    feature_root = tmp_path / "plugins-d"
    repo_root.mkdir()
    _git(repo_root, "init", "--initial-branch", "release/main", "--quiet")
    _git(repo_root, "config", "user.email", "test@example.invalid")
    _git(repo_root, "config", "user.name", "Test")
    (repo_root / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo_root, "add", "README.md")
    _git(repo_root, "commit", "-m", "seed", "--quiet")
    _git(repo_root, "update-ref", "refs/remotes/origin/release/main", "HEAD")
    _git(
        repo_root,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/release/main",
    )
    _git(repo_root, "branch", "work/manage-runtime-marketplaces")
    _git(
        repo_root,
        "worktree",
        "add",
        "--quiet",
        str(feature_root),
        "work/manage-runtime-marketplaces",
    )

    monkeypatch.chdir(feature_root)

    assert sync_module._real_source_root() == repo_root


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


def test_single_flight_lock_claim_exposes_owner_body(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_identity=lambda pid: f"identity:{pid}",
    )

    claim = single_flight.acquire()

    assert claim.acquired is True
    assert sync_module._read_lock_owner_body(
        single_flight.lock_path.read_text(encoding="utf-8"),
    ) == sync_module._LockOwner(
        pid=os.getpid(),
        identity=f"identity:{os.getpid()}",
    )
    assert list(state_dir.glob(f"{sync_module.SYNC_LOCK_FILENAME}.*.tmp")) == []


def test_single_flight_rejects_malformed_pid_lock_body() -> None:
    lock_body = (
        f'{{"{sync_module.LOCK_OWNER_PID_FIELD}": {sync_module.MAX_LOCK_OWNER_PID + 1}, '
        f'"{sync_module.LOCK_OWNER_IDENTITY_FIELD}": "oversized"}}'
    )

    assert sync_module._read_lock_owner_body(lock_body) is None


def test_real_process_identity_observes_live_and_exited_process() -> None:
    child = subprocess.Popen(
        [sys.executable, "-c", "import signal\nsignal.pause()"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert sync_module._process_exists(child.pid)
        identity = sync_module._process_identity(child.pid)
        assert identity is not None
        assert f"pid:{child.pid}:started:" in identity
    finally:
        child.terminate()
        child.wait(timeout=5)

    assert not sync_module._process_exists(child.pid)
    assert sync_module._process_identity(child.pid) is None


def test_process_is_zombie_reads_zombie_process_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_pid = os.getpid()

    def run_process(
        argv: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        assert argv == ["ps", "-p", str(owner_pid), "-o", "state="]
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == sync_module.PROCESS_STATE_TIMEOUT_SECONDS
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=f"{sync_module.ZOMBIE_PROCESS_STATE_PREFIX}+\n",
            stderr="",
        )

    monkeypatch.setattr(sync_module.subprocess, "run", run_process)

    assert sync_module._process_is_zombie(owner_pid) is True


def test_process_is_zombie_treats_process_state_failures_as_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_pid = os.getpid()

    def run_process(
        argv: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        assert argv == ["ps", "-p", str(owner_pid), "-o", "state="]
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == sync_module.PROCESS_STATE_TIMEOUT_SECONDS
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="missing")

    monkeypatch.setattr(sync_module.subprocess, "run", run_process)

    assert sync_module._process_is_zombie(owner_pid) is False


def test_process_is_zombie_treats_process_state_timeout_as_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_pid = os.getpid()

    def run_process(
        argv: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        assert argv == ["ps", "-p", str(owner_pid), "-o", "state="]
        assert check is False
        assert capture_output is True
        assert text is True
        assert timeout == sync_module.PROCESS_STATE_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, timeout)

    monkeypatch.setattr(sync_module.subprocess, "run", run_process)

    assert sync_module._process_is_zombie(owner_pid) is False


def test_no_distribution_changes_with_healthy_topology_skips_refresh() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe()
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )

    assert exit_code == 0
    assert runner.calls == []
    assert config_repairer.calls == 1
    assert change_probe.queries == [SCRIPTED_BASE_REF]
    assert topology_probe.calls == 1
    assert single_flight.acquisitions == 0
    assert single_flight.releases == 0


def test_invalid_topology_runs_refresh_without_distribution_changes() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(errors=DEFAULT_TOPOLOGY_ERRORS)
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert change_probe.queries == [SCRIPTED_BASE_REF]
    assert topology_probe.calls == 1
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1
    assert runner.calls == list(STEP_ARGVS)


def test_active_single_flight_records_pending_and_exits_zero(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_identity=lambda pid: f"identity:{pid}",
    )
    active_claim = single_flight.acquire()
    assert active_claim.acquired is True
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(errors=DEFAULT_TOPOLOGY_ERRORS)

    try:
        exit_code = sync(
            SCRIPTED_BASE_REF,
            runner=runner,
            tool_probe=tool_probe,
            change_probe=change_probe,
            config_repairer=config_repairer,
            topology_probe=topology_probe,
            single_flight=single_flight,
        )

        assert exit_code == 0
        assert runner.calls == []
        assert topology_probe.calls == 1
        assert single_flight.lock_path.exists()
        pending_owner = single_flight.pending_path.read_text(encoding="utf-8")
        assert sync_module._read_lock_owner_body(
            pending_owner
        ) == sync_module._LockOwner(
            pid=os.getpid(),
            identity=f"identity:{os.getpid()}",
        )
    finally:
        single_flight.release()
    assert not single_flight.pending_path.exists()


@pytest.mark.parametrize(
    ("distribution_changed", "config_changed", "expected_message"),
    [
        pytest.param(
            True,
            False,
            "change-driven sync cannot skip refresh",
            id="distribution-change",
        ),
        pytest.param(
            False,
            True,
            "configuration repair cannot skip refresh",
            id="config-repair",
        ),
    ],
)
def test_validation_required_sync_fails_when_refresh_is_active(
    distribution_changed: bool,
    config_changed: bool,
    expected_message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=distribution_changed)
    config_repairer = ScriptedConfigRepairer(changed=config_changed)
    single_flight = ScriptedSingleFlight(
        claim=sync_module.SingleFlightClaim(
            acquired=False,
            pending_recorded=True,
            blocked_by_active_owner=True,
        ),
    )

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert expected_message in captured.err
    assert runner.calls == []
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 0
    assert change_probe.queries == ([SCRIPTED_BASE_REF] if distribution_changed else [])


def test_absent_base_ref_fails_when_refresh_is_active(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    single_flight = ScriptedSingleFlight(
        claim=sync_module.SingleFlightClaim(
            acquired=False,
            pending_recorded=True,
            blocked_by_active_owner=True,
        ),
    )

    exit_code = sync(
        None,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no-baseline sync cannot skip refresh" in captured.err
    assert runner.calls == []
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 0
    assert change_probe.queries == []


def test_changed_single_flight_lock_exits_nonzero_without_refresh(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(errors=DEFAULT_TOPOLOGY_ERRORS)
    single_flight = ScriptedSingleFlight(
        claim=sync_module.SingleFlightClaim(acquired=False),
    )

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Marketplace refresh lock changed during acquisition" in captured.err
    assert runner.calls == []
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 0


def test_pending_cleanup_failure_releases_newly_acquired_lock(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_identity=lambda pid: f"identity:{pid}",
    )
    single_flight.pending_path.mkdir()
    runner = RecordingRunner()

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE),
        change_probe=ScriptedChangeProbe(changed=True),
        config_repairer=ScriptedConfigRepairer(changed=False),
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Marketplace refresh lock failed:" in captured.err
    assert runner.calls == []
    assert not single_flight.lock_path.exists()
    assert single_flight.pending_path.is_dir()


def test_refresh_release_failure_exits_nonzero_after_successful_steps(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=True)
    config_repairer = ScriptedConfigRepairer(changed=False)
    single_flight = ScriptedSingleFlight(
        release_error=OSError("permission denied"),
    )

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Marketplace refresh lock release failed: permission denied" in captured.err
    assert runner.calls == list(STEP_ARGVS)
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1


def test_file_single_flight_release_reports_lock_read_failure(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_identity=lambda pid: f"identity:{pid}",
    )
    runner = RecordingRunner()

    def corrupt_lock_then_succeed(argv: Sequence[str]) -> int:
        result = runner(argv)
        if single_flight.lock_path.is_file():
            single_flight.lock_path.unlink()
            single_flight.lock_path.mkdir()
        return result

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=corrupt_lock_then_succeed,
        tool_probe=ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE),
        change_probe=ScriptedChangeProbe(changed=True),
        config_repairer=ScriptedConfigRepairer(changed=False),
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Marketplace refresh lock release failed:" in captured.err
    assert runner.calls == list(STEP_ARGVS)
    assert single_flight.lock_path.is_dir()


def test_refresh_release_failure_supersedes_step_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner(exit_codes=(7,))
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=True)
    config_repairer = ScriptedConfigRepairer(changed=False)
    single_flight = ScriptedSingleFlight(
        release_error=OSError("permission denied"),
    )

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Marketplace refresh lock release failed: permission denied" in captured.err
    assert runner.calls == [STEP_ARGVS[0]]
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1


def test_invalid_single_flight_lock_is_replaced(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_exists=lambda _pid: False,
    )
    single_flight.lock_path.write_text("999999\n", encoding="utf-8")

    run = run_invalid_topology_refresh(single_flight)

    assert run.exit_code == 0
    assert run.observed_no_change_invalid_topology_probe
    assert run.runner.calls == list(STEP_ARGVS)
    assert not single_flight.lock_path.exists()
    assert not single_flight.pending_path.exists()


def test_absent_single_flight_owner_lock_is_replaced(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_exists=lambda _pid: False,
        process_identity=lambda pid: f"identity:{pid}",
    )
    missing_owner = sync_module._LockOwner(pid=999999, identity="absent")
    stale_pending_owner = sync_module._LockOwner(pid=999998, identity="pending")
    single_flight.lock_path.write_text(
        sync_module._serialize_lock_owner(missing_owner),
        encoding="utf-8",
    )
    single_flight.pending_path.write_text(
        sync_module._serialize_lock_owner(stale_pending_owner),
        encoding="utf-8",
    )

    run = run_invalid_topology_refresh(single_flight)

    assert run.exit_code == 0
    assert run.observed_no_change_invalid_topology_probe
    assert run.runner.calls == list(STEP_ARGVS)
    assert not single_flight.lock_path.exists()
    assert not single_flight.pending_path.exists()


def test_stale_single_flight_unlink_preserves_replacement_lock(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    stale_owner = sync_module._LockOwner(pid=999999, identity="stale")
    replacement_owner = sync_module._LockOwner(pid=os.getpid(), identity="replacement")
    lock_path = state_dir / sync_module.SYNC_LOCK_FILENAME
    lock_path.write_text(
        sync_module._serialize_lock_owner(stale_owner),
        encoding="utf-8",
    )

    def process_exists(pid: int) -> bool:
        if pid == stale_owner.pid:
            lock_path.write_text(
                sync_module._serialize_lock_owner(replacement_owner),
                encoding="utf-8",
            )
            return False
        return pid == replacement_owner.pid

    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_exists=process_exists,
        process_identity=lambda pid: (
            "replacement" if pid == replacement_owner.pid else None
        ),
    )

    claim = single_flight.acquire()

    assert claim.acquired is False
    assert claim.pending_recorded is True
    assert claim.blocked_by_active_owner is True
    assert single_flight.lock_path.read_text(
        encoding="utf-8"
    ) == sync_module._serialize_lock_owner(replacement_owner)
    assert single_flight.pending_path.exists()


def test_single_flight_replaces_reused_pid_lock(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_exists=lambda _pid: True,
        process_identity=lambda pid: f"current:{pid}",
    )
    reused_pid_owner = sync_module._LockOwner(
        pid=os.getpid(),
        identity=f"previous:{os.getpid()}",
    )
    single_flight.lock_path.write_text(
        sync_module._serialize_lock_owner(reused_pid_owner),
        encoding="utf-8",
    )

    run = run_invalid_topology_refresh(single_flight)

    assert run.exit_code == 0
    assert run.observed_no_change_invalid_topology_probe
    assert run.runner.calls == list(STEP_ARGVS)
    assert not single_flight.lock_path.exists()
    assert not single_flight.pending_path.exists()


def test_single_flight_unresolved_live_owner_records_pending(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    live_owner = sync_module._LockOwner(pid=999999, identity="unresolved")

    def process_identity(pid: int) -> str | None:
        if pid == os.getpid():
            return f"identity:{pid}"
        return None

    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_exists=lambda _pid: True,
        process_identity=process_identity,
    )
    single_flight.lock_path.write_text(
        sync_module._serialize_lock_owner(live_owner),
        encoding="utf-8",
    )

    run = run_invalid_topology_refresh(single_flight)

    assert run.exit_code == 0
    assert run.observed_no_change_invalid_topology_probe
    assert run.runner.calls == []
    assert single_flight.lock_path.read_text(
        encoding="utf-8",
    ) == sync_module._serialize_lock_owner(live_owner)
    assert sync_module._read_lock_owner_body(
        single_flight.pending_path.read_text(encoding="utf-8"),
    ) == sync_module._LockOwner(
        pid=os.getpid(),
        identity=f"identity:{os.getpid()}",
    )


def test_single_flight_release_clears_pending_marker(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_identity=lambda pid: f"identity:{pid}",
    )
    owner_claim = single_flight.acquire()
    assert owner_claim.acquired is True
    follower_claim = single_flight.acquire()
    assert follower_claim.acquired is False
    assert follower_claim.pending_recorded is True

    single_flight.release()

    assert not single_flight.lock_path.exists()
    assert not single_flight.pending_path.exists()


def test_single_flight_identity_lookup_failure_exits_before_refresh(
    tmp_path: pathlib.Path,
) -> None:
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_identity=lambda _pid: None,
    )

    run = run_invalid_topology_refresh(single_flight)

    assert run.exit_code == 1
    assert run.observed_no_change_invalid_topology_probe
    assert run.runner.calls == []
    assert not single_flight.lock_path.exists()
    assert not single_flight.pending_path.exists()


def test_single_flight_treats_zombie_owner_lock_as_stale(
    tmp_path: pathlib.Path,
) -> None:
    zombie_owner = sync_module._LockOwner(pid=999999, identity="zombie")
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_exists=lambda _pid: True,
        process_identity=lambda pid: (
            f"identity:{pid}" if pid == os.getpid() else zombie_owner.identity
        ),
        process_is_zombie=lambda pid: pid == zombie_owner.pid,
    )
    single_flight.lock_path.write_text(
        sync_module._serialize_lock_owner(zombie_owner),
        encoding="utf-8",
    )

    run = run_invalid_topology_refresh(single_flight)

    assert run.exit_code == 0
    assert run.observed_no_change_invalid_topology_probe
    assert run.runner.calls == list(STEP_ARGVS)
    assert not single_flight.lock_path.exists()
    assert not single_flight.pending_path.exists()


def test_single_flight_treats_vanished_owner_lock_as_stale(
    tmp_path: pathlib.Path,
) -> None:
    vanished_owner = sync_module._LockOwner(pid=999999, identity="vanished")
    state_dir = tmp_path / "outcomeeng"
    state_dir.mkdir()
    process_exists_results = iter([True, False])
    single_flight = _FileSingleFlight(
        state_dir=state_dir,
        process_exists=lambda _pid: next(process_exists_results),
        process_identity=lambda pid: f"identity:{pid}" if pid == os.getpid() else None,
    )
    single_flight.lock_path.write_text(
        sync_module._serialize_lock_owner(vanished_owner),
        encoding="utf-8",
    )

    run = run_invalid_topology_refresh(single_flight)

    assert run.exit_code == 0
    assert run.observed_no_change_invalid_topology_probe
    assert run.runner.calls == list(STEP_ARGVS)
    assert not single_flight.lock_path.exists()
    assert not single_flight.pending_path.exists()


def test_topology_probe_failure_exits_before_refresh(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(error=InstalledSetError("bad json"))
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Codex cache topology check failed: bad json" in captured.err
    assert "Marketplace refresh has no active owner" in captured.err
    assert runner.calls == []
    assert config_repairer.calls == 1
    assert change_probe.queries == [SCRIPTED_BASE_REF]
    assert topology_probe.calls == 1
    assert single_flight.observations == 1
    assert single_flight.acquisitions == 0
    assert single_flight.releases == 0


def test_topology_filesystem_failure_exits_before_refresh(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(error=OSError("permission denied"))
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Codex cache topology check failed: permission denied" in captured.err
    assert "Marketplace refresh has no active owner" in captured.err
    assert runner.calls == []
    assert config_repairer.calls == 1
    assert change_probe.queries == [SCRIPTED_BASE_REF]
    assert topology_probe.calls == 1
    assert single_flight.observations == 1
    assert single_flight.acquisitions == 0
    assert single_flight.releases == 0


@pytest.mark.parametrize(
    "topology_error",
    [
        pytest.param(InstalledSetError("bad json"), id="installed-set-error"),
        pytest.param(OSError("permission denied"), id="filesystem-error"),
    ],
)
def test_topology_failure_coalesces_with_active_refresh(
    topology_error: Exception,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(error=topology_error)
    single_flight = ScriptedSingleFlight(
        observation_claim=sync_module.SingleFlightClaim(
            acquired=False,
            pending_recorded=True,
            blocked_by_active_owner=True,
            detail="pid:123",
        ),
    )

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"Codex cache topology check failed: {topology_error}" in captured.err
    assert "Marketplace refresh already running" in captured.out
    assert "Active sync: pid:123" in captured.out
    assert runner.calls == []
    assert config_repairer.calls == 1
    assert change_probe.queries == [SCRIPTED_BASE_REF]
    assert topology_probe.calls == 1
    assert single_flight.observations == 1
    assert single_flight.acquisitions == 0
    assert single_flight.releases == 0


def test_topology_failure_without_pending_marker_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(error=OSError("permission denied"))
    single_flight = ScriptedSingleFlight(
        observation_claim=sync_module.SingleFlightClaim(
            acquired=False,
            pending_recorded=False,
            blocked_by_active_owner=True,
            detail="pid:123",
        ),
    )

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Codex cache topology check failed: permission denied" in captured.err
    assert "Marketplace refresh pending marker was not recorded" in captured.err
    assert runner.calls == []
    assert config_repairer.calls == 1
    assert change_probe.queries == [SCRIPTED_BASE_REF]
    assert topology_probe.calls == 1
    assert single_flight.observations == 1
    assert single_flight.acquisitions == 0
    assert single_flight.releases == 0


def test_topology_failure_exits_nonzero_when_lock_observation_fails(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    topology_probe = ScriptedTopologyProbe(error=InstalledSetError("bad json"))
    single_flight = ScriptedSingleFlight(
        observe_error=OSError("state unavailable"),
    )

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        topology_probe=topology_probe,
        single_flight=single_flight,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Codex cache topology check failed: bad json" in captured.err
    assert (
        "Marketplace refresh lock observation failed: state unavailable" in captured.err
    )
    assert runner.calls == []
    assert config_repairer.calls == 1
    assert change_probe.queries == [SCRIPTED_BASE_REF]
    assert topology_probe.calls == 1
    assert single_flight.observations == 1
    assert single_flight.acquisitions == 0
    assert single_flight.releases == 0


def test_config_repair_runs_refresh_without_consulting_distribution_changes() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=True)
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert change_probe.queries == []
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1
    assert runner.calls == list(STEP_ARGVS)


def test_distribution_changes_invoke_all_steps_in_declared_order() -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=True)
    config_repairer = ScriptedConfigRepairer(changed=False)
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        SCRIPTED_BASE_REF,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1
    assert runner.calls == list(STEP_ARGVS)


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
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        None,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert runner.calls == list(STEP_ARGVS)
    assert change_probe.queries == []
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1


@pytest.mark.parametrize("base_ref", ["", None])
def test_empty_base_ref_treated_as_no_baseline(base_ref: str | None) -> None:
    runner = RecordingRunner()
    tool_probe = ScriptedToolProbe(available=ALL_TOOLS_AVAILABLE)
    change_probe = ScriptedChangeProbe(changed=False)
    config_repairer = ScriptedConfigRepairer(changed=False)
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        base_ref,
        runner=runner,
        tool_probe=tool_probe,
        change_probe=change_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert runner.calls == list(STEP_ARGVS)
    assert change_probe.queries == []
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1


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
    single_flight = ScriptedSingleFlight()

    exit_code = sync(
        base_ref,
        runner=runner,
        tool_probe=tool_probe,
        config_repairer=config_repairer,
        single_flight=single_flight,
    )

    assert exit_code == 0
    assert config_repairer.calls == 1
    assert single_flight.acquisitions == 1
    assert single_flight.releases == 1
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
    changed_file = _probe_target(tmp_path, path_root)
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


def _probe_target(repo: pathlib.Path, path_root: str) -> pathlib.Path:
    root = pathlib.Path(path_root)
    if root.suffix:
        return repo / root
    return repo / root / "distribution-probe.txt"

"""Scenario tests for the worktree-local audit state surface.

Exercises the surface end-to-end — `state_transition`, `save_state`,
`load_state`, `RunLock`, `branch_slug` — at the level the audit-
orchestrator agent invokes them, one run at a time. The per-helper
scenarios live in the parent enabler's ``tests/test_auditing.scenario.l1.py``;
this file proves the helpers compose into the contract the spec asserts.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
from types import ModuleType
from typing import Any

import pytest

# parents[5] = repo root (this file lives 5 levels deep under spx/).
SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[5]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "auditing"
    / "scripts"
)
AUDIT_ORCHESTRATOR = SCRIPTS_DIR / "audit_orchestrator.py"

SAMPLE_BRANCH = "feature/state-surface"
SHA_RUN_1 = "1111111"
SHA_RUN_2 = "2222222"
SHA_RUN_3 = "3333333"
TS_RUN_1 = "2026-05-11T15:30:00Z"
TS_RUN_2 = "2026-05-11T16:00:00Z"
TS_RUN_3 = "2026-05-11T17:00:00Z"
REJECTED_VERDICT = "REJECTED"
APPROVED_VERDICT = "APPROVED"

LOCK_TTL = 600
LOCK_AGE_FRESH = 60
LOCK_AGE_STALE = 1200


def _load_audit_orchestrator() -> ModuleType:
    """Load audit_orchestrator.py from its plugin path via importlib."""
    spec = importlib.util.spec_from_file_location(
        "audit_orchestrator", AUDIT_ORCHESTRATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {AUDIT_ORCHESTRATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_orchestrator"] = module
    spec.loader.exec_module(module)
    return module


def _finding(
    file_line: str,
    root_cause: str,
    required_fix: str,
    concern: str = "comprehension",
) -> dict[str, str]:
    return {
        "file_line": file_line,
        "concern": concern,
        "root_cause": root_cause,
        "required_fix": required_fix,
    }


def _state_path(tmp_path: pathlib.Path, lang: str = "python") -> pathlib.Path:
    return tmp_path / ".spx" / "audits" / lang / "main.md"


def test_first_run_creates_state_with_monotonic_ids(tmp_path: pathlib.Path) -> None:
    """First run on a branch creates the state file with f-001, f-002, ..."""
    module = _load_audit_orchestrator()
    state_path = _state_path(tmp_path)

    result = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SHA_RUN_1,
        now=TS_RUN_1,
        verdict=REJECTED_VERDICT,
        new_findings=[
            _finding("src/a.py:1", "tangles IO", "extract helper"),
            _finding("src/b.py:2", "missing guard", "add validation"),
        ],
    )

    assert [f["id"] for f in result["open"]] == ["f-001", "f-002"]
    assert state_path.exists()
    state = module.load_state(state_path)
    assert state is not None
    assert state.next_finding_id == 3


def test_carry_forward_preserves_id_and_refreshes_required_fix(
    tmp_path: pathlib.Path,
) -> None:
    """A finding present in both runs keeps its ID; required_fix refreshes."""
    module = _load_audit_orchestrator()
    state_path = _state_path(tmp_path)

    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SHA_RUN_1,
        now=TS_RUN_1,
        verdict=REJECTED_VERDICT,
        new_findings=[_finding("src/a.py:1", "tangles IO", "v1")],
    )
    second = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SHA_RUN_2,
        now=TS_RUN_2,
        verdict=REJECTED_VERDICT,
        new_findings=[_finding("src/a.py:1", "tangles IO", "v2")],
    )

    assert [f["id"] for f in second["open"]] == ["f-001"]
    assert second["open"][0]["required_fix"] == "v2"
    state = module.load_state(state_path)
    assert state is not None
    assert state.next_finding_id == 2  # never advanced for carry-over


def test_absence_resolves_open_finding_with_run_sha(tmp_path: pathlib.Path) -> None:
    """An open finding missing from the new run resolves with resolved_at = SHA."""
    module = _load_audit_orchestrator()
    state_path = _state_path(tmp_path)

    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SHA_RUN_1,
        now=TS_RUN_1,
        verdict=REJECTED_VERDICT,
        new_findings=[_finding("src/a.py:1", "tangles IO", "fix")],
    )
    second = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SHA_RUN_2,
        now=TS_RUN_2,
        verdict=APPROVED_VERDICT,
        new_findings=[],
    )

    assert [r["id"] for r in second["resolved"]] == ["f-001"]
    assert second["resolved"][0]["resolved_at"] == SHA_RUN_2


def test_regression_reopens_original_id_without_advancing_counter(
    tmp_path: pathlib.Path,
) -> None:
    """A root cause returning at the same file:line reopens the original ID."""
    module = _load_audit_orchestrator()
    state_path = _state_path(tmp_path)
    payload = _finding("src/a.py:1", "tangles IO", "fix")

    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SHA_RUN_1,
        now=TS_RUN_1,
        verdict=REJECTED_VERDICT,
        new_findings=[payload],
    )
    module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SHA_RUN_2,
        now=TS_RUN_2,
        verdict=APPROVED_VERDICT,
        new_findings=[],
    )
    third = module.state_transition(
        state_path=state_path,
        branch=SAMPLE_BRANCH,
        current_sha=SHA_RUN_3,
        now=TS_RUN_3,
        verdict=REJECTED_VERDICT,
        new_findings=[_finding("src/a.py:1", "tangles IO", "fix again")],
    )

    assert [f["id"] for f in third["reopened"]] == ["f-001"]
    state = module.load_state(state_path)
    assert state is not None
    assert state.next_finding_id == 2


class _FakeClock:
    """Monotonic time source whose value the test controls."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.time = start

    def __call__(self) -> float:
        return self.time


def test_fresh_lock_refuses_second_run(tmp_path: pathlib.Path) -> None:
    """A lock file with mtime inside the TTL blocks a second acquisition."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / ".spx" / "audits" / "python" / "main.md.lock"
    clock = _FakeClock()

    outer = module.RunLock(lock_path, max_age_seconds=LOCK_TTL, now=clock)
    outer.__enter__()
    try:
        clock.time += LOCK_AGE_FRESH
        with (
            pytest.raises(module.RunLockError),
            module.RunLock(lock_path, max_age_seconds=LOCK_TTL, now=clock),
        ):
            pass
    finally:
        outer.__exit__(None, None, None)
    assert not lock_path.exists()


def test_stale_lock_is_overwritten(tmp_path: pathlib.Path) -> None:
    """A lock older than the TTL is overwritten by the next acquisition."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / ".spx" / "audits" / "python" / "main.md.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    clock = _FakeClock()

    lock_path.write_text(str(clock.time))
    stale_time = clock.time - LOCK_AGE_STALE
    os.utime(lock_path, (stale_time, stale_time))

    with module.RunLock(lock_path, max_age_seconds=LOCK_TTL, now=clock):
        assert lock_path.exists()


def test_atomic_save_state_keeps_prior_file_intact_on_rename_failure(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed os.replace leaves the prior state file unchanged."""
    module = _load_audit_orchestrator()
    state_path = _state_path(tmp_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("prior content", encoding="utf-8")

    class ReplaceFailed(OSError):
        pass

    def failing_replace(src: object, dst: object) -> None:
        raise ReplaceFailed(f"simulated rename failure: {src} -> {dst}")

    monkeypatch.setattr(module.os, "replace", failing_replace)

    new_state = module.AuditState(
        branch=SAMPLE_BRANCH,
        first_run_sha=SHA_RUN_1,
        first_run_at=TS_RUN_1,
        last_run_sha=SHA_RUN_1,
        last_run_at=TS_RUN_1,
        last_verdict=APPROVED_VERDICT,
        run_count=1,
        next_finding_id=1,
    )

    with pytest.raises(ReplaceFailed):
        module.save_state(new_state, state_path)

    assert state_path.read_text(encoding="utf-8") == "prior content"


def test_lock_released_on_exception_path(tmp_path: pathlib.Path) -> None:
    """The lock file is removed even when the wrapped block raises."""
    module = _load_audit_orchestrator()
    lock_path = tmp_path / ".spx" / "audits" / "python" / "main.md.lock"
    clock = _FakeClock()

    class _Boom(RuntimeError):
        pass

    with (
        pytest.raises(_Boom),
        module.RunLock(lock_path, max_age_seconds=LOCK_TTL, now=clock),
    ):
        raise _Boom("simulated audit failure")

    assert not lock_path.exists()


def test_spx_root_is_gitignored() -> None:
    """The ``.spx/`` partition root is gitignored at the repo level.

    The state-surface spec carries an ALWAYS assertion that audit
    state never enters the commit history. A stale ``.gitignore``
    rebase that silently dropped the entry would let state files
    leak into product truth on the next ``git add``. Guard against
    that by checking the on-disk ``.gitignore`` against the assertion.
    """
    # parents[5] = repo root, matching the SCRIPTS_DIR derivation.
    repo_root = pathlib.Path(__file__).resolve().parents[5]
    gitignore = repo_root / ".gitignore"
    assert gitignore.is_file(), f"expected .gitignore at {gitignore}"
    entries = {
        line.strip()
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert ".spx/" in entries, (
        f".gitignore must list '.spx/'; current entries: {sorted(entries)}"
    )


def test_branch_slug_collision_separates_state_files(tmp_path: pathlib.Path) -> None:
    """A branch literally named like another branch's slug lands on a distinct path."""
    module = _load_audit_orchestrator()
    state_dir = tmp_path / ".spx" / "audits" / "python"
    state_dir.mkdir(parents=True, exist_ok=True)

    # First branch's state lives at the base slug.
    (state_dir / "feature__foo.md").write_text(
        "---\nbranch: feature/foo\n---\n\n# state\n", encoding="utf-8"
    )

    colliding_slug: Any = module.branch_slug("feature__foo", state_dir)

    assert "--" in colliding_slug
    assert colliding_slug.startswith("feature__foo--")

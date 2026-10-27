"""L3 end-to-end scenario for 13-agent-environment.enabler (agent-environment.md).

L3: the shipped `hooks.json` command runs through `/bin/sh` against the real
`spx` CLI in a real git worktree, with the test process standing in as the
session's controlling process. It is the fullest reproduction of a real
SessionStart: no env stubbing of spx's effects, and the claim is verified by
asking spx itself — `spx worktree status` — whether it recognizes the worktree
as running, closing the round-trip rather than inspecting a claim file on disk.

Assertion covered (agent-environment.md, L3 scenario):
  - The hook delegates to spx, which writes each session-environment variable to
    `$CLAUDE_ENV_FILE` with its correct value and records a worktree-occupancy
    claim that `spx worktree status` reports as `running`.
"""

from __future__ import annotations

import os
from pathlib import Path

from outcomeeng_testing.harnesses.hooks import (
    WORKTREE_CLAIMED_ENV,
    WORKTREE_CLAIM_PATH_ENV,
    WORKTREE_CONTROLLING_PID_ENV,
    has_worktree_claim_export,
    init_session_worktree,
    read_env_exports,
    run_session_start,
    worktree_claim_path_from_env,
    worktree_occupancy,
)

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_session_start_delivers_correct_env_and_a_claim_spx_recognizes(
    tmp_path: Path,
) -> None:
    init_session_worktree(tmp_path)
    env_file = tmp_path / "claude.env"

    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
        # The test process is the session's controlling process: alive when spx
        # reads liveness below, so its claim resolves to `running`, not `free`.
        env_overrides={WORKTREE_CONTROLLING_PID_ENV: str(os.getpid())},
    )
    assert result.returncode == 0

    # spx canonicalizes the project dir (on macOS /var -> /private/var), so the
    # oracle for the two project-dir variables is the resolved path.
    project_dir = str(tmp_path.resolve())
    env = read_env_exports(
        env_file,
        [
            "CLAUDE_SESSION_ID",
            "CLAUDE_PROJECT_DIR",
            "PROJECT_DIR",
            WORKTREE_CLAIMED_ENV,
            WORKTREE_CLAIM_PATH_ENV,
        ],
    )
    assert env["CLAUDE_SESSION_ID"] == SESSION_ID
    assert env["CLAUDE_PROJECT_DIR"] == project_dir
    assert env["PROJECT_DIR"] == project_dir
    assert has_worktree_claim_export(env)
    claim_path = worktree_claim_path_from_env(env_file, tmp_path)
    assert claim_path.parent == tmp_path.resolve() / ".spx" / "worktrees"
    assert claim_path.exists()

    # The round-trip: spx itself recognizes the worktree the hook claimed.
    occupancy = worktree_occupancy(tmp_path)
    assert len(occupancy) == 1
    assert occupancy[0]["status"] == "running"

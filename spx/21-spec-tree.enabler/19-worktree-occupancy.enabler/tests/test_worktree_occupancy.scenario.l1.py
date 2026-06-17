"""
Scenario tests for 19-worktree-occupancy.enabler (worktree-occupancy.md scenarios).

Both tests run at L1: the real `session-start` hook subprocess, a fake `spx`
executable that records its argv and cwd (a spy at the hook→CLI boundary), and
real filesystem I/O in pytest tmp_path directories.

The hook delegates the claim to the `spx` CLI via $SPX_BIN — the marketplace
defines the `spx worktree claim` invocation; the `spx` repo implements the
command and the claim's `.spx/worktrees/` I/O. These tests pin the marketplace
side: the hook records a claim for the running worktree when the CLI is present,
and degrades to a silent no-op when it is absent, fails, or hangs.

Assertions covered:
  - SessionStart records a worktree-occupancy claim for the running worktree by
    invoking `spx worktree claim` against that worktree (CLI present).
  - SessionStart records no claim and degrades to a silent no-op when the `spx`
    CLI is absent or exits non-zero; the claim is bounded by a timeout so a hung
    spx is also a no-op rather than a stalled session start.
"""

import json
import subprocess
from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.hooks import (
    MISSING_SPX,
    make_spec_tree,
    run_pretool_gate,
    run_session_start,
)


def _fake_spx(bindir: Path, *, returncode: int = 0) -> Path:
    """Write a fake `spx` executable that records its argv and cwd.

    The argv (everything after `spx`) is written to `<spx>.argv` as a JSON list
    and the working directory to `<spx>.cwd`, so a test can assert how and where
    the hook invoked the CLI.
    """
    bindir.mkdir(parents=True, exist_ok=True)
    spx = bindir / "spx"
    spx.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, pathlib, sys\n"
        'pathlib.Path(__file__ + ".argv").write_text(json.dumps(sys.argv[1:]))\n'
        'pathlib.Path(__file__ + ".cwd").write_text(os.getcwd())\n'
        f"sys.exit({returncode})\n"
    )
    spx.chmod(0o755)
    return spx


def _slow_fake_spx(bindir: Path, *, sleep_seconds: float) -> Path:
    """Write a fake `spx` that sleeps before recording its argv.

    When the hook's claim timeout fires first, the process is killed mid-sleep
    and the `<spx>.argv` marker is never written — a test reads its absence as
    "the claim was abandoned".
    """
    bindir.mkdir(parents=True, exist_ok=True)
    spx = bindir / "spx"
    spx.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys, time\n"
        f"time.sleep({sleep_seconds})\n"
        'pathlib.Path(__file__ + ".argv").write_text(json.dumps(sys.argv[1:]))\n'
        "sys.exit(0)\n"
    )
    spx.chmod(0o755)
    return spx


def _session_start(
    project_dir: Path, session_id: str, *, spx_bin: str
) -> subprocess.CompletedProcess:
    # The canonical hook harness runs the real session-start.py; SPX_BIN selects
    # the spx the worktree claim delegates to (a fake spy or a missing binary).
    return run_session_start(
        {"session_id": session_id, "cwd": str(project_dir)},
        project_dir=project_dir,
        env_overrides={"SPX_BIN": spx_bin},
    )


def _argv(spx: Path) -> list[str]:
    return json.loads(Path(str(spx) + ".argv").read_text())


def _recorded_cwd(spx: Path) -> Path:
    return Path(Path(str(spx) + ".cwd").read_text())


def _fake_spx_with_worktree_status(
    bindir: Path,
    *,
    status: str,
    claim_returncode: int = 0,
    claim_stderr: str = "",
) -> Path:
    """Write a fake `spx` that records each hook-delegated subcommand."""
    bindir.mkdir(parents=True, exist_ok=True)
    spx = bindir / "spx"
    spx.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        "calls_path = pathlib.Path(__file__ + '.calls')\n"
        "calls = json.loads(calls_path.read_text()) if calls_path.exists() else []\n"
        "args = sys.argv[1:]\n"
        "calls.append(args)\n"
        "calls_path.write_text(json.dumps(calls))\n"
        "if args[:3] == ['worktree', 'status', '--format']:\n"
        f"    print(json.dumps({{'worktree': 'worktree', 'status': {status!r}}}))\n"
        "    sys.exit(0)\n"
        "if args[:2] == ['worktree', 'claim']:\n"
        f"    sys.stderr.write({claim_stderr!r})\n"
        f"    sys.exit({claim_returncode})\n"
        "if args[:2] == ['gate', 'check']:\n"
        "    print(json.dumps({'decision': 'allow', 'reason': ''}))\n"
        "    sys.exit(0)\n"
        "sys.exit(2)\n"
    )
    spx.chmod(0o755)
    return spx


def _calls(spx: Path) -> list[list[str]]:
    return json.loads(Path(str(spx) + ".calls").read_text())


def _pretool_payload(project_dir: Path, *, session_id: str = "sess-pretool") -> dict:
    return {
        "session_id": session_id,
        "transcript_path": str(project_dir / "transcript.jsonl"),
        "cwd": str(project_dir),
        "tool_name": "Read",
        "tool_input": {"file_path": "spx/thing.product.md"},
    }


def _hook_output(result: subprocess.CompletedProcess) -> dict | None:
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]


# ---------------------------------------------------------------------------
# Assertion 1 — SessionStart records a claim for the running worktree
# ---------------------------------------------------------------------------


class TestSessionStartRecordsWorktreeClaim:
    def test_invokes_spx_worktree_claim_for_the_running_worktree(self, tmp_path):
        project_dir = tmp_path / "worktree"
        project_dir.mkdir()
        spx = _fake_spx(tmp_path / "bin")
        session_id = "test-session-abc123"

        result = _session_start(project_dir, session_id, spx_bin=str(spx))

        assert result.returncode == 0
        argv = _argv(spx)
        assert argv[:2] == ["worktree", "claim"]
        assert "--session-id" in argv
        assert argv[argv.index("--session-id") + 1] == session_id
        # The claim targets the running worktree (the hook's project directory).
        assert _recorded_cwd(spx).resolve() == project_dir.resolve()
        # The claim's output must never reach stdout, which is injected into the
        # agent's context; a non-git worktree yields no base-staleness directive.
        assert result.stdout == ""

    def test_invokes_claim_with_codex_thread_identity_fallback(self, tmp_path):
        project_dir = tmp_path / "worktree"
        project_dir.mkdir()
        spx = _fake_spx(tmp_path / "bin")
        session_id = "019ed48b-0465-79b2-ba88-8bf2838cd71a"

        result = run_session_start(
            {"cwd": str(project_dir)},
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx), "CODEX_THREAD_ID": session_id},
        )

        assert result.returncode == 0
        argv = _argv(spx)
        assert argv[:2] == ["worktree", "claim"]
        assert argv[argv.index("--session-id") + 1] == session_id

    # The guard `(payload.get("session_id") or "").strip()` reads every "no
    # session identity" shape as empty: an empty string, an absent key, and a
    # whitespace-only value. Each case runs in its own pytest tmp_path with its
    # own spy, so a misfire is attributed to the exact shape that caused it.
    @pytest.mark.parametrize(
        "session_field",
        [{"session_id": ""}, {}, {"session_id": "   "}],
        ids=["empty", "absent", "whitespace"],
    )
    def test_no_claim_when_session_identity_absent(self, tmp_path, session_field):
        project_dir = tmp_path / "worktree"
        project_dir.mkdir()
        spx = _fake_spx(tmp_path / "bin")

        result = run_session_start(
            {**session_field, "cwd": str(project_dir)},
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        assert result.stdout == ""
        # With no identity to key the claim on, the hook never invokes the CLI.
        assert not Path(str(spx) + ".argv").exists()

    def test_no_claim_when_project_dir_absent(self, tmp_path):
        spx = _fake_spx(tmp_path / "bin")

        # A valid session id but no project directory — no `cwd` in the payload
        # and no CLAUDE_PROJECT_DIR in the env — leaves no worktree to target,
        # so the guard skips the claim.
        result = run_session_start(
            {"session_id": "sess-p"},
            project_dir=None,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert not Path(str(spx) + ".argv").exists()


# ---------------------------------------------------------------------------
# Assertion 2 — absent or failing spx degrades to a silent no-op
# ---------------------------------------------------------------------------


class TestSessionStartDegradesWithoutSpx:
    def test_missing_spx_is_silent_noop(self, tmp_path):
        project_dir = tmp_path / "worktree"
        project_dir.mkdir()

        result = _session_start(project_dir, "sess-x", spx_bin=MISSING_SPX)

        assert result.returncode == 0
        assert result.stdout == ""

    def test_nonzero_spx_is_silent_noop(self, tmp_path):
        project_dir = tmp_path / "worktree"
        project_dir.mkdir()
        spx = _fake_spx(tmp_path / "bin", returncode=1)

        result = _session_start(project_dir, "sess-y", spx_bin=str(spx))

        assert result.returncode == 0
        assert result.stdout == ""

    def test_hung_spx_is_silent_noop(self, tmp_path):
        project_dir = tmp_path / "worktree"
        project_dir.mkdir()
        # The fake sleeps well past the overridden claim timeout, so the hook
        # abandons the claim instead of stalling session start.
        spx = _slow_fake_spx(tmp_path / "bin", sleep_seconds=3)

        result = run_session_start(
            {"session_id": "sess-z", "cwd": str(project_dir)},
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx), "SPX_TIMEOUT_SECONDS": "0.3"},
        )

        assert result.returncode == 0
        assert result.stdout == ""
        # The claim timed out and was killed mid-sleep: the spy never recorded.
        assert not Path(str(spx) + ".argv").exists()


# ---------------------------------------------------------------------------
# Assertion 3 — PreToolUse repairs stale or unclaimed occupancy
# ---------------------------------------------------------------------------


class TestPreToolUseRepairsWorktreeClaim:
    @pytest.mark.parametrize("status", ["stale", "unclaimed"])
    def test_reclaims_stale_or_unclaimed_worktree_before_gate(self, tmp_path, status):
        project_dir = tmp_path / "worktree"
        make_spec_tree(project_dir)
        spx = _fake_spx_with_worktree_status(tmp_path / "bin", status=status)
        session_id = "019ed48b-0465-79b2-ba88-8bf2838cd71a"

        result = run_pretool_gate(
            _pretool_payload(project_dir, session_id=session_id),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        assert _calls(spx) == [
            ["worktree", "status", "--format", "json"],
            ["worktree", "claim", "--session-id", session_id],
            [
                "gate",
                "check",
                "--tool",
                "Read",
                "--session-id",
                session_id,
                "--transcript",
                str(project_dir / "transcript.jsonl"),
                "--path",
                "spx/thing.product.md",
            ],
        ]
        output = _hook_output(result)
        assert output is not None
        assert output["hookEventName"] == "PreToolUse"
        assert session_id in output["additionalContext"]
        assert status in output["additionalContext"]

    def test_surfaces_failed_claim_diagnostic(self, tmp_path):
        project_dir = tmp_path / "worktree"
        make_spec_tree(project_dir)
        spx = _fake_spx_with_worktree_status(
            tmp_path / "bin",
            status="stale",
            claim_returncode=1,
            claim_stderr="Error: worktree controlling process could not be resolved\n",
        )
        session_id = "019ed48b-0465-79b2-ba88-8bf2838cd71a"

        result = run_pretool_gate(
            _pretool_payload(project_dir, session_id=session_id),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        output = _hook_output(result)
        assert output is not None
        assert "automatic claim repair failed" in output["additionalContext"]
        assert (
            "worktree controlling process could not be resolved"
            in output["additionalContext"]
        )

    def test_leaves_occupied_worktree_claim_untouched(self, tmp_path):
        project_dir = tmp_path / "worktree"
        make_spec_tree(project_dir)
        spx = _fake_spx_with_worktree_status(tmp_path / "bin", status="occupied")

        result = run_pretool_gate(
            _pretool_payload(project_dir),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        assert _calls(spx) == [
            ["worktree", "status", "--format", "json"],
            [
                "gate",
                "check",
                "--tool",
                "Read",
                "--session-id",
                "sess-pretool",
                "--transcript",
                str(project_dir / "transcript.jsonl"),
                "--path",
                "spx/thing.product.md",
            ],
        ]
        assert _hook_output(result) is None

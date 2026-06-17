"""
Scenario tests for 54-load-gating.enabler (load-gating.md scenarios).

Each test runs the real `load-gate` PreToolUse hook subprocess against a fake
`spx` executable that records its argv and cwd (a spy at the hook->CLI boundary)
and prints a crafted verdict, plus real filesystem I/O in pytest tmp_path
directories.

The hook delegates the verdict to the `spx` CLI via $SPX_BIN — the marketplace
defines the `spx gate` invocation and emits the verdict; the `spx` repo
implements the command, the boundary-scoped transcript scan, and the path-to-node
mapping. These tests pin the marketplace side: the hook emits the CLI's
deny/allow verdict, degrades to allowing the call when the CLI is absent, no-ops
outside a spec-tree repository, and forwards the locators without reading the
transcript itself.

Assertions covered (load-gating.md → Scenarios):
  - deny verdict -> the hook emits a PreToolUse deny decision carrying the message
  - allow verdict -> the hook emits no denial
  - absent / non-zero / hung spx -> the hook degrades to allowing the call
  - non-spec-tree repository -> the hook allows and does not invoke the CLI
  - the hook forwards the tool name, path argument, session id, and transcript
    path, and reads neither the transcript nor any .spx/ file itself
"""

import json
from pathlib import Path

from outcomeeng_testing.harnesses.hooks import MISSING_SPX, run_pretool_gate


def _spec_tree_project(tmp_path: Path) -> Path:
    """Create a project directory that classifies as a spec-tree repository."""
    project_dir = tmp_path / "worktree"
    (project_dir / "spx").mkdir(parents=True)
    (project_dir / "spx" / "thing.product.md").write_text("# Product\n")
    return project_dir


def _fake_spx(
    bindir: Path, *, decision: str = "allow", reason: str = "", returncode: int = 0
) -> Path:
    """Write a fake `spx` that records argv/cwd and prints a crafted verdict.

    The argv (everything after `spx`) is written to `<spx>.argv` as JSON and the
    working directory to `<spx>.cwd`, so a test can assert how and where the hook
    invoked the CLI. The verdict the hook parses is printed to stdout.
    """
    bindir.mkdir(parents=True, exist_ok=True)
    spx = bindir / "spx"
    spx.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, pathlib, sys\n"
        'pathlib.Path(__file__ + ".argv").write_text(json.dumps(sys.argv[1:]))\n'
        'pathlib.Path(__file__ + ".cwd").write_text(os.getcwd())\n'
        f"print(json.dumps({{'decision': {decision!r}, 'reason': {reason!r}}}))\n"
        f"sys.exit({returncode})\n"
    )
    spx.chmod(0o755)
    return spx


def _slow_fake_spx(bindir: Path, *, sleep_seconds: float) -> Path:
    """Write a fake `spx` that sleeps past the gate timeout before recording."""
    bindir.mkdir(parents=True, exist_ok=True)
    spx = bindir / "spx"
    spx.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys, time\n"
        f"time.sleep({sleep_seconds})\n"
        'pathlib.Path(__file__ + ".argv").write_text(json.dumps(sys.argv[1:]))\n'
        "print(json.dumps({'decision': 'deny', 'reason': 'late'}))\n"
        "sys.exit(0)\n"
    )
    spx.chmod(0o755)
    return spx


def _argv(spx: Path) -> list[str]:
    return json.loads(Path(str(spx) + ".argv").read_text())


def _recorded_cwd(spx: Path) -> Path:
    return Path(Path(str(spx) + ".cwd").read_text())


def _payload(
    project_dir: Path,
    *,
    tool_name: str = "Read",
    tool_input: dict | None = None,
    session_id: str = "sess-1",
    transcript_path: str = "/some/transcript.jsonl",
) -> dict:
    return {
        "session_id": session_id,
        "transcript_path": transcript_path,
        "cwd": str(project_dir),
        "tool_name": tool_name,
        "tool_input": tool_input if tool_input is not None else {},
    }


def _decision(result) -> dict | None:
    """Parse the hook's PreToolUse decision, or None when it emitted nothing."""
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]


class TestGateEmitsCliVerdict:
    def test_deny_verdict_blocks_with_message(self, tmp_path):
        project_dir = _spec_tree_project(tmp_path)
        spx = _fake_spx(
            tmp_path / "bin",
            decision="deny",
            reason="load /spec-tree:understand first",
        )

        result = run_pretool_gate(
            _payload(project_dir, tool_name="Read"),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        decision = _decision(result)
        assert decision is not None
        assert decision["hookEventName"] == "PreToolUse"
        assert decision["permissionDecision"] == "deny"
        assert (
            decision["permissionDecisionReason"] == "load /spec-tree:understand first"
        )

    def test_allow_verdict_emits_no_denial(self, tmp_path):
        project_dir = _spec_tree_project(tmp_path)
        spx = _fake_spx(tmp_path / "bin", decision="allow")

        result = run_pretool_gate(
            _payload(project_dir, tool_name="Read"),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        assert _decision(result) is None


class TestGateDegradesToAllow:
    def test_missing_spx_allows(self, tmp_path):
        project_dir = _spec_tree_project(tmp_path)

        result = run_pretool_gate(
            _payload(project_dir),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": MISSING_SPX},
        )

        assert result.returncode == 0
        assert _decision(result) is None

    def test_nonzero_spx_allows(self, tmp_path):
        project_dir = _spec_tree_project(tmp_path)
        spx = _fake_spx(tmp_path / "bin", decision="deny", reason="x", returncode=1)

        result = run_pretool_gate(
            _payload(project_dir),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        # A non-zero exit is a CLI error, not a verdict — degrade to allow.
        assert _decision(result) is None

    def test_hung_spx_allows(self, tmp_path):
        project_dir = _spec_tree_project(tmp_path)
        spx = _slow_fake_spx(tmp_path / "bin", sleep_seconds=3)

        result = run_pretool_gate(
            _payload(project_dir),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx), "SPX_GATE_TIMEOUT_SECONDS": "0.3"},
        )

        assert result.returncode == 0
        assert _decision(result) is None
        assert not Path(str(spx) + ".argv").exists()

    def test_unparseable_verdict_allows(self, tmp_path):
        # The CLI exits zero but prints stdout that is not a JSON verdict — the
        # hook cannot read a decision from it, so it degrades to allowing the call.
        project_dir = _spec_tree_project(tmp_path)
        bindir = tmp_path / "bin"
        bindir.mkdir(parents=True, exist_ok=True)
        spx = bindir / "spx"
        spx.write_text(
            "#!/usr/bin/env python3\nimport sys\nprint('not a json verdict')\nsys.exit(0)\n"
        )
        spx.chmod(0o755)

        result = run_pretool_gate(
            _payload(project_dir),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        assert _decision(result) is None

    def test_no_tool_name_allows(self, tmp_path):
        # A payload with no tool name has nothing to gate on — the hook allows the
        # call and never reaches the CLI.
        project_dir = _spec_tree_project(tmp_path)
        spx = _fake_spx(tmp_path / "bin", decision="deny", reason="should not run")

        result = run_pretool_gate(
            {
                "session_id": "sess-1",
                "transcript_path": "/some/transcript.jsonl",
                "cwd": str(project_dir),
                "tool_input": {},
            },
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        assert _decision(result) is None
        assert not Path(str(spx) + ".argv").exists()


class TestGateOutsideSpecTree:
    def test_non_spec_tree_repo_allows_without_invoking_cli(self, tmp_path):
        project_dir = tmp_path / "plain"
        project_dir.mkdir()
        spx = _fake_spx(tmp_path / "bin", decision="deny", reason="should not run")

        result = run_pretool_gate(
            _payload(project_dir),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        assert _decision(result) is None
        # No spx/*.product.md present — the gate never reaches the CLI.
        assert not Path(str(spx) + ".argv").exists()


class TestGateForwardsLocators:
    def test_forwards_tool_path_session_and_transcript(self, tmp_path):
        project_dir = _spec_tree_project(tmp_path)
        spx = _fake_spx(tmp_path / "bin", decision="allow")
        edited = "spx/21-spec-tree.enabler/13-agent-environment.enabler/x.md"
        # A transcript path that does not exist: if the hook read it itself the
        # call would change behavior; forwarding it proves the hook delegates.
        missing_transcript = str(tmp_path / "no-such-transcript.jsonl")

        result = run_pretool_gate(
            _payload(
                project_dir,
                tool_name="Edit",
                tool_input={"file_path": edited},
                session_id="sess-fwd",
                transcript_path=missing_transcript,
            ),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        argv = _argv(spx)
        assert argv[:2] == ["gate", "check"]
        assert argv[argv.index("--tool") + 1] == "Edit"
        assert argv[argv.index("--session-id") + 1] == "sess-fwd"
        assert argv[argv.index("--transcript") + 1] == missing_transcript
        assert argv[argv.index("--path") + 1] == edited
        # The gate ran against the running worktree and never read the transcript.
        assert _recorded_cwd(spx).resolve() == project_dir.resolve()

    def test_forwards_bash_command_as_path_argument(self, tmp_path):
        # A Bash call carries its path-bearing argument as `command`, not
        # `file_path` — the gate forwards it via --command so the CLI maps a
        # mutating shell command (git commit/push/mv) to its owning node.
        project_dir = _spec_tree_project(tmp_path)
        spx = _fake_spx(tmp_path / "bin", decision="allow")
        command = "git mv spx/a spx/b"

        result = run_pretool_gate(
            _payload(
                project_dir,
                tool_name="Bash",
                tool_input={"command": command},
            ),
            project_dir=project_dir,
            env_overrides={"SPX_BIN": str(spx)},
        )

        assert result.returncode == 0
        argv = _argv(spx)
        assert argv[argv.index("--tool") + 1] == "Bash"
        assert argv[argv.index("--command") + 1] == command

"""Property tests for 13-agent-environment.enabler (agent-environment.md property).

L1: the real `session-start.py` hook is run as a subprocess against real
filesystem I/O in pytest tmp_path directories, with no test doubles.

Assertion covered:
  - For any session UUID, the env file receives exactly that value as
    $CLAUDE_SESSION_ID — the identity round-trips unchanged through the hook's
    shell-quoting.
"""

import shlex
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.hooks import run_session_start

_EXPORT_PREFIX = "export CLAUDE_SESSION_ID="

# Session ids are single-line tokens; exclude control characters (which include
# newlines and nulls) so the value occupies one shell `export` line. shlex
# quoting must still round-trip spaces, quotes, and other shell metacharacters.
_session_ids = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc")),
    min_size=1,
).filter(lambda value: value.strip() != "")


@given(session_id=_session_ids)
def test_session_id_round_trips_through_env_file(session_id):
    # A fresh temp dir per generated input — a function-scoped fixture would not
    # reset between Hypothesis examples.
    with tempfile.TemporaryDirectory() as scratch:
        env_file = Path(scratch) / "claude.env"
        run_session_start(
            {"session_id": session_id, "cwd": scratch},
            env_file=env_file,
            project_dir=scratch,
        )
        exported = [
            line
            for line in env_file.read_text(encoding="utf-8").splitlines()
            if line.startswith(_EXPORT_PREFIX)
        ]
    assert exported, "hook wrote no CLAUDE_SESSION_ID export line"
    recovered = shlex.split(exported[-1][len(_EXPORT_PREFIX) :])[0]
    assert recovered == session_id.strip()


def _exported_identity_line(env_file: Path) -> str:
    lines = [
        line
        for line in env_file.read_text(encoding="utf-8").splitlines()
        if line.startswith(_EXPORT_PREFIX)
    ]
    assert lines, "hook wrote no CLAUDE_SESSION_ID export line"
    return lines[-1]


@given(session_id=_session_ids)
def test_session_id_write_is_deterministic(session_id):
    # The same payload must yield the same export line every run, so every Bash
    # call in a session that sources the env file observes one stable identity.
    with tempfile.TemporaryDirectory() as scratch:
        first = Path(scratch) / "first.env"
        second = Path(scratch) / "second.env"
        for env_file in (first, second):
            run_session_start(
                {"session_id": session_id, "cwd": scratch},
                env_file=env_file,
                project_dir=scratch,
            )
        assert _exported_identity_line(first) == _exported_identity_line(second)

"""Property test for 21-identity.enabler (identity.md properties).

L1: runs ``spx hooks session-start`` as a subprocess. For any session UUID the env
file receives that identity (whitespace trimmed), and the write is deterministic —
the same payload yields the same env-file line every run.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

import shlex
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.hooks import run_session_start

_KEY = "CLAUDE_SESSION_ID="

# The hook is a real subprocess, so each example's runtime is dominated by
# interpreter startup — disable hypothesis's per-example deadline so host load
# never raises a spurious DeadlineExceeded.
_subprocess_property = settings(deadline=None)

# Session ids are single-line tokens; exclude control characters so the value
# occupies one env-file line.
_session_ids = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc")),
    min_size=1,
).filter(lambda value: value.strip() != "")


def _identity_line(env_file: Path) -> str:
    lines = [
        line
        for line in env_file.read_text(encoding="utf-8").splitlines()
        if _KEY in line
    ]
    assert lines, "hook wrote no CLAUDE_SESSION_ID line"
    return lines[-1]


def _recovered_identity(env_file: Path) -> str:
    line = _identity_line(env_file)
    return shlex.split(line[line.index(_KEY) + len(_KEY) :])[0]


@_subprocess_property
@given(session_id=_session_ids)
def test_session_id_round_trips_through_env_file(session_id) -> None:
    with tempfile.TemporaryDirectory() as scratch:
        env_file = Path(scratch) / "claude.env"
        run_session_start(
            {"session_id": session_id, "cwd": scratch},
            env_file=env_file,
            project_dir=scratch,
        )
        assert _recovered_identity(env_file) == session_id.strip()


@_subprocess_property
@given(session_id=_session_ids)
def test_session_id_write_is_deterministic(session_id) -> None:
    with tempfile.TemporaryDirectory() as scratch:
        first = Path(scratch) / "first.env"
        second = Path(scratch) / "second.env"
        for env_file in (first, second):
            run_session_start(
                {"session_id": session_id, "cwd": scratch},
                env_file=env_file,
                project_dir=scratch,
            )
        assert _identity_line(first) == _identity_line(second)

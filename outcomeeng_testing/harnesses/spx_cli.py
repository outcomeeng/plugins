"""Harness: a fake ``spx`` CLI for driving hook subprocess calls.

Mediates access to a controlled ``spx`` executable so a test can exercise the
real ``session-start.py`` hook's ``spx session todo`` read without the real CLI
or a test double. Owns the fake executable's creation, the data it returns, an
invocation log, and cleanup — it does not replace the hook's behavior, only the
external command the hook shells out to.

The fake reads its response from the environment the hook passes through, so a
single static executable serves every case:

  ``FAKE_SPX_TODO``       JSON array of session records ``session todo`` returns
                          (wrapped as ``{"todo": [...]}``, matching the real
                          ``--fields`` projection).
  ``FAKE_SPX_TODO_EXIT``  exit code ``session todo`` returns (non-zero models a
                          failing CLI).
  ``FAKE_SPX_LOG``        path the fake appends each invocation's argv to, so a
                          test can assert which subcommands ran.

Any other subcommand (the hook's ``worktree claim``) is a logged no-op exiting
zero. Exception case per
``plugins/spec-tree/skills/testing/references/methodology.md``: none.
"""

from __future__ import annotations

import json
import shutil
import stat
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

_FAKE_SPX_SOURCE = '''\
#!/usr/bin/env python3
"""Fake spx CLI — see outcomeeng_testing/harnesses/spx_cli.py."""
import json
import os
import sys

args = sys.argv[1:]

log = os.environ.get("FAKE_SPX_LOG")
if log:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(args) + "\\n")

if args[:2] == ["session", "todo"]:
    exit_code = int(os.environ.get("FAKE_SPX_TODO_EXIT", "0"))
    if exit_code != 0:
        sys.exit(exit_code)
    todo = json.loads(os.environ.get("FAKE_SPX_TODO", "[]"))
    print(json.dumps({"todo": todo}))
    sys.exit(0)

# Any other subcommand (e.g. the hook's `worktree claim`) is a logged no-op.
sys.exit(0)
'''


@dataclass(frozen=True)
class FakeSpx:
    """Handle to a fake ``spx`` executable and its invocation log."""

    bin_path: Path
    log_path: Path
    _todo: tuple[dict[str, str], ...]
    _todo_exit: int

    @property
    def env(self) -> dict[str, str]:
        """Environment overrides for ``run_session_start`` that wire in this fake."""
        return {
            "SPX_BIN": str(self.bin_path),
            "FAKE_SPX_LOG": str(self.log_path),
            "FAKE_SPX_TODO": json.dumps(list(self._todo)),
            "FAKE_SPX_TODO_EXIT": str(self._todo_exit),
        }

    def invocations(self) -> list[list[str]]:
        """Every argv the fake was invoked with, in call order."""
        if not self.log_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def session_invocations(self) -> list[list[str]]:
        """Only the ``session`` subcommand invocations, in call order."""
        return [argv for argv in self.invocations() if argv[:1] == ["session"]]


@contextmanager
def fake_spx(
    *,
    todo: Sequence[dict[str, str]] | None = None,
    todo_exit_code: int = 0,
) -> Iterator[FakeSpx]:
    """Yield a :class:`FakeSpx` whose ``session todo`` returns ``todo``.

    ``todo`` is the session-record list the projection wraps as
    ``{"todo": [...]}``; an empty or omitted list models an empty queue.
    ``todo_exit_code`` forces a non-zero ``session todo`` to model a failing CLI.
    The fake executable and its log live in a temporary directory removed on
    every exit path, including exceptions.
    """
    scratch = Path(tempfile.mkdtemp(prefix="fake-spx-"))
    try:
        bin_path = scratch / "spx"
        bin_path.write_text(_FAKE_SPX_SOURCE, encoding="utf-8")
        bin_path.chmod(
            bin_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        yield FakeSpx(
            bin_path=bin_path,
            log_path=scratch / "invocations.log",
            _todo=tuple(todo or ()),
            _todo_exit=todo_exit_code,
        )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def sample_todo_session(**overrides: str) -> dict[str, str]:
    """Return a representative `spx session todo` record for the fake queue.

    A single claimable-session record the fake CLI projects; pass keyword
    overrides to vary individual fields (for example a distinct ``id`` or
    ``git_ref``). The values are test-authored input the directive echoes, not
    source-owned production constants.
    """
    record = {
        "id": "2026-06-15_19-21-23",
        "priority": "medium",
        "goal": "Build the discoverability hook",
        "next_step": "Invoke /understanding then /contextualizing",
        "git_ref": "feat/session-start-discoverability",
    }
    record.update(overrides)
    return record


__all__ = ["FakeSpx", "fake_spx", "sample_todo_session"]

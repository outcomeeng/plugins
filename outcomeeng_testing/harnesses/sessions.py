"""Real-command harness for the sessions enabler's scenario evidence.

The harness owns temporary session storage, ``spx session`` command assembly,
the JSON-prefix handoff payload, output parsing, and reusable scenario inputs.
Tests retain the assertion flow while the real ``spx`` binary, git repositories,
and filesystem provide the behavior and oracle at ``l1``.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

SUCCESS_EXIT: Final = 0
SINGLE_RESULT_COUNT: Final = 1
MULTI_SESSION_COUNT: Final = 2

ACTIVE_NODE: Final = "spx/21-spec-tree.enabler/76-sessions.enabler/"
SESSION_BODY: Final = "# Session\n"
ACTIVE_NODE_BODY: Final = f"Active node: {ACTIVE_NODE}\n"
SPECIFIC_CONTENT_BODY: Final = "# Session with specific content\n\nKeep this intact."
PLAN_EXCERPT: Final = "## PLAN: Wire the spx CLI half of the session-scope accumulator"
ISSUES_EXCERPT: Final = (
    "## 12. Repo-wide evidence links still contain legacy test naming"
)
PLAN_BODY: Final = f"# Session with PLAN.md\n\n{PLAN_EXCERPT}\n"
ISSUES_BODY: Final = f"# Session with ISSUES.md\n\n{ISSUES_EXCERPT}\n"
ABSENT_WORK_BRANCH: Final = "work/absent"

HANDOFF_BASE_ERROR: Final = "SessionHandoffBaseError"
WORK_BRANCH_NOT_ON_ORIGIN_ERROR: Final = "SessionWorkBranchNotOnOriginError"

DEFAULT_PRIORITY: Final = "medium"
DEFAULT_GOAL: Final = "Verify handoff behavior"
DEFAULT_NEXT_STEP: Final = "Inspect the session file"
PRIORITY_FIELD: Final = "priority"
GOAL_FIELD: Final = "goal"
NEXT_STEP_FIELD: Final = "next_step"
GIT_REF_FIELD: Final = "git_ref"

TODO_QUEUE: Final = "todo"
DOING_QUEUE: Final = "doing"
SESSION_SUFFIX: Final = ".md"

HANDOFF_ID_PATTERN: Final = re.compile(r"<HANDOFF_ID>(.+?)</HANDOFF_ID>")
SESSION_FILE_PATTERN: Final = re.compile(r"<SESSION_FILE>(.+?)</SESSION_FILE>")
GIT_REF_PATTERN: Final = re.compile(
    r'^\s*"?git_ref"?:\s*"?([^"\n]+?)"?\s*$', re.MULTILINE
)


@dataclass(frozen=True)
class SessionCommandHarness:
    """Invoke real session commands against isolated storage and git context."""

    sessions_dir: Path
    cwd: Path

    def handoff(
        self,
        body: str = SESSION_BODY,
        *,
        priority: str = DEFAULT_PRIORITY,
        goal: str = DEFAULT_GOAL,
        next_step: str = DEFAULT_NEXT_STEP,
        git_ref: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Create a handoff using the CLI's JSON-header-plus-body wire format."""
        fields = {
            PRIORITY_FIELD: priority,
            GOAL_FIELD: goal,
            NEXT_STEP_FIELD: next_step,
        }
        if git_ref is not None:
            fields[GIT_REF_FIELD] = git_ref
        payload = f"{json.dumps(fields)}\n{body}"
        return self._run(("handoff",), input_text=payload)

    def pickup(self, session_id: str) -> subprocess.CompletedProcess[str]:
        """Move one session from todo to doing."""
        return self._run(("pickup", session_id))

    def release(self, *session_ids: str) -> subprocess.CompletedProcess[str]:
        """Move one or more sessions from doing to todo."""
        return self._run(("release", *session_ids))

    def create_and_pickup(self, body: str = SESSION_BODY) -> str:
        """Create one session, move it to doing, and return its identifier."""
        handoff = self.handoff(body)
        _require_success(handoff)
        session_id = self.handoff_id(handoff.stdout)
        _require_success(self.pickup(session_id))
        return session_id

    def create_picked_up_batch(self) -> tuple[str, ...]:
        """Create the finite multi-release scenario batch in doing."""
        return tuple(
            self.create_and_pickup(f"# Session {index}\n")
            for index in range(MULTI_SESSION_COUNT)
        )

    def queue_files(self, queue: str) -> tuple[Path, ...]:
        """Return session Markdown files in a queue."""
        return tuple(sorted((self.sessions_dir / queue).glob(f"*{SESSION_SUFFIX}")))

    def session_path(self, queue: str, session_id: str) -> Path:
        """Return the canonical path for one queued session."""
        return self.sessions_dir / queue / f"{session_id}{SESSION_SUFFIX}"

    @staticmethod
    def handoff_id(stdout: str) -> str:
        """Extract the session identifier emitted by ``spx session handoff``."""
        match = HANDOFF_ID_PATTERN.search(stdout)
        if match is None:
            raise AssertionError(f"no <HANDOFF_ID> in: {stdout}")
        return match.group(1)

    @staticmethod
    def session_file(stdout: str) -> Path:
        """Extract the session-file path emitted by ``spx session handoff``."""
        match = SESSION_FILE_PATTERN.search(stdout)
        if match is None:
            raise AssertionError(f"no <SESSION_FILE> in: {stdout}")
        return Path(match.group(1))

    @staticmethod
    def git_ref(session_file: Path) -> str:
        """Read the serialized ``git_ref`` value from a session document."""
        match = GIT_REF_PATTERN.search(session_file.read_text())
        if match is None:
            raise AssertionError(f"no git_ref in frontmatter of {session_file}")
        return match.group(1)

    def _run(
        self, args: tuple[str, ...], *, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["spx", "session", *args, "--sessions-dir", str(self.sessions_dir)]
            if args[0] == "handoff"
            else [
                "spx",
                "session",
                args[0],
                "--sessions-dir",
                str(self.sessions_dir),
                *args[1:],
            ],
            input=input_text,
            capture_output=True,
            text=True,
            cwd=self.cwd,
        )


@contextmanager
def session_commands(cwd: Path) -> Iterator[SessionCommandHarness]:
    """Yield isolated real session commands rooted at ``cwd``."""
    with TemporaryDirectory() as tmp:
        yield SessionCommandHarness(sessions_dir=Path(tmp), cwd=cwd)


def current_branch(repo: Path) -> str:
    """Return the current branch name from a real git repository."""
    return subprocess.run(
        ["git", "-C", str(repo), "branch", "--show-current"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _require_success(result: subprocess.CompletedProcess[str]) -> None:
    if result.returncode != SUCCESS_EXIT:
        raise AssertionError(result.stderr)


__all__ = [
    "ABSENT_WORK_BRANCH",
    "ACTIVE_NODE",
    "ACTIVE_NODE_BODY",
    "DOING_QUEUE",
    "HANDOFF_BASE_ERROR",
    "ISSUES_BODY",
    "ISSUES_EXCERPT",
    "MULTI_SESSION_COUNT",
    "PLAN_BODY",
    "PLAN_EXCERPT",
    "SESSION_BODY",
    "SINGLE_RESULT_COUNT",
    "SPECIFIC_CONTENT_BODY",
    "SUCCESS_EXIT",
    "TODO_QUEUE",
    "WORK_BRANCH_NOT_ON_ORIGIN_ERROR",
    "SessionCommandHarness",
    "current_branch",
    "session_commands",
]

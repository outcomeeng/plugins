"""Real-command infrastructure for the sessions enabler's scenario evidence.

The harness owns temporary session storage, ``spx session`` command assembly,
resource cleanup, output parsing, and fixture-path access. Complete handoff
requests live as inert fixture files; the real ``spx`` binary, git repositories,
and filesystem provide behavior and oracles at ``l1``.
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

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
)
from outcomeeng_testing.harnesses.verify_session_claims import (
    load_verify_session_claims_module,
)

FIXTURE_ROOT: Final = Path(__file__).resolve().parents[1] / "fixtures" / "sessions"
BASIC_HANDOFF_FIXTURE: Final = FIXTURE_ROOT / "basic-handoff.txt"
ACTIVE_NODE_HANDOFF_FIXTURE: Final = FIXTURE_ROOT / "active-node-handoff.txt"
SPECIFIC_CONTENT_HANDOFF_FIXTURE: Final = FIXTURE_ROOT / "specific-content-handoff.txt"
PLAN_HANDOFF_FIXTURE: Final = FIXTURE_ROOT / "plan-handoff.txt"
ISSUES_HANDOFF_FIXTURE: Final = FIXTURE_ROOT / "issues-handoff.txt"
WORK_BRANCH_HANDOFF_FIXTURE: Final = FIXTURE_ROOT / "work-branch-handoff.txt"

OUTPUT_MARKER_PATTERN: Final = re.compile(
    r"<(?P<marker>[A-Z_]+)>(?P<value>.+?)</(?P=marker)>"
)


class SessionHarnessError(RuntimeError):
    """Report an invalid infrastructure observation or fixture contract."""


@dataclass(frozen=True)
class HandoffPayload:
    """One whole JSON-header-plus-body input loaded from an inert fixture."""

    header: dict[str, object]
    body: str

    @classmethod
    def from_path(cls, path: Path) -> HandoffPayload:
        """Read one complete handoff fixture without importing fixture code."""
        header_line, body = path.read_text().split("\n", maxsplit=1)
        header = json.loads(header_line)
        if not isinstance(header, dict):
            raise TypeError(f"handoff fixture header is not an object: {path}")
        return cls(header=header, body=body)

    def with_placeholder_value(self, value: str) -> HandoffPayload:
        """Fill the fixture's sole null field with a generated scenario value."""
        placeholder_fields = [
            key for key, field_value in self.header.items() if field_value is None
        ]
        if len(placeholder_fields) != 1:
            raise ValueError("handoff fixture must contain exactly one null field")
        header = dict(self.header)
        header[placeholder_fields[0]] = value
        return HandoffPayload(header=header, body=self.body)

    def wire_text(self) -> str:
        """Render the CLI's JSON-line prefix followed by body bytes."""
        return f"{json.dumps(self.header)}\n{self.body}"


@dataclass(frozen=True)
class SessionRecord:
    """A session identifier paired with the path emitted at creation time."""

    session_id: str
    initial_path: Path

    @property
    def todo_path(self) -> Path:
        """Return the path emitted for the initial todo-queue record."""
        return self.initial_path

    @property
    def doing_path(self) -> Path:
        """Return the corresponding path in the active queue."""
        return self.initial_path.parent.parent / "doing" / self.initial_path.name


@dataclass(frozen=True)
class SessionCommandHarness:
    """Invoke real session commands against isolated storage and git context."""

    sessions_dir: Path
    cwd: Path

    def handoff(
        self,
        payload: HandoffPayload | None = None,
        *,
        work_branch: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Create a handoff from an inert whole-payload fixture."""
        selected = payload if payload is not None else basic_handoff_payload()
        if work_branch is not None:
            selected = work_branch_handoff_payload().with_placeholder_value(work_branch)
        return self._run(("handoff",), input_text=selected.wire_text())

    def pickup(self, record: SessionRecord) -> subprocess.CompletedProcess[str]:
        """Move one created session into the active queue."""
        return self._run(("pickup", record.session_id))

    def release(self, *records: SessionRecord) -> subprocess.CompletedProcess[str]:
        """Move one or more active sessions back to their initial queue."""
        return self._run(("release", *(record.session_id for record in records)))

    def show(self, record: SessionRecord) -> subprocess.CompletedProcess[str]:
        """Read one session through the CLI's structured session API."""
        return self._run(("show", "--json", record.session_id))

    def created_session(
        self, result: subprocess.CompletedProcess[str]
    ) -> SessionRecord:
        """Resolve the emitted absolute session path and derive its identifier."""
        candidates = [
            Path(match.group("value"))
            for match in OUTPUT_MARKER_PATTERN.finditer(result.stdout)
            if Path(match.group("value")).is_absolute()
        ]
        if len(candidates) != 1:
            raise SessionHarnessError(
                f"expected one emitted session path, observed: {result.stdout}"
            )
        path = candidates[0]
        return SessionRecord(session_id=path.stem, initial_path=path)

    def session_files(self) -> tuple[Path, ...]:
        """Return every file the isolated session store contains."""
        return tuple(
            sorted(path for path in self.sessions_dir.rglob("*") if path.is_file())
        )

    @staticmethod
    def parse_git_ref(result: subprocess.CompletedProcess[str]) -> str | None:
        """Parse the git ref from a structured session-show observation."""
        payload = json.loads(result.stdout)
        if isinstance(payload, list):
            if len(payload) != 1 or not isinstance(payload[0], dict):
                raise SessionHarnessError(
                    "session show returned an unexpected record list"
                )
            payload = payload[0]
        if not isinstance(payload, dict):
            raise SessionHarnessError("session show returned an unexpected record")
        module = load_verify_session_claims_module()
        value = payload.get(module.SESSION_GIT_REF_FIELD)
        return value if isinstance(value, str) else None

    def _run(
        self, args: tuple[str, ...], *, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        command = [
            "spx",
            "session",
            args[0],
            "--sessions-dir",
            str(self.sessions_dir),
            *args[1:],
        ]
        return subprocess.run(
            command,
            input=input_text,
            capture_output=True,
            text=True,
            cwd=self.cwd,
        )


def basic_handoff_payload() -> HandoffPayload:
    return HandoffPayload.from_path(BASIC_HANDOFF_FIXTURE)


def active_node_handoff_payload() -> HandoffPayload:
    return HandoffPayload.from_path(ACTIVE_NODE_HANDOFF_FIXTURE)


def specific_content_handoff_payload() -> HandoffPayload:
    return HandoffPayload.from_path(SPECIFIC_CONTENT_HANDOFF_FIXTURE)


def plan_handoff_payload() -> HandoffPayload:
    return HandoffPayload.from_path(PLAN_HANDOFF_FIXTURE)


def issues_handoff_payload() -> HandoffPayload:
    return HandoffPayload.from_path(ISSUES_HANDOFF_FIXTURE)


def work_branch_handoff_payload() -> HandoffPayload:
    return HandoffPayload.from_path(WORK_BRANCH_HANDOFF_FIXTURE)


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


@contextmanager
def accepted_session_commands() -> Iterator[SessionCommandHarness]:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        yield commands


__all__ = [
    "HandoffPayload",
    "SessionCommandHarness",
    "SessionHarnessError",
    "SessionRecord",
    "accepted_session_commands",
    "active_node_handoff_payload",
    "basic_handoff_payload",
    "current_branch",
    "issues_handoff_payload",
    "plan_handoff_payload",
    "session_commands",
    "specific_content_handoff_payload",
    "work_branch_handoff_payload",
]

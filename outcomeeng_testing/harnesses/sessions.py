"""Real-command infrastructure for the sessions enabler's scenario evidence.

The harness owns temporary session storage, ``spx session`` command assembly,
resource cleanup, and output parsing. Generated request values come from the
sessions generator, while the real ``spx`` binary, git repositories, and
filesystem provide behavior and observations at ``l1``.
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

from outcomeeng_testing.generators.sessions import (
    HandoffPayload,
    generated_handoff_batch,
    generated_handoff_payload,
)
from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
)
from outcomeeng_testing.harnesses.verify_session_claims import (
    load_verify_session_claims_module,
)

OUTPUT_MARKER_PATTERN: Final = re.compile(
    r"<(?P<marker>[A-Z_]+)>(?P<value>.+?)</(?P=marker)>"
)
HANDOFF_REQUIRED_FIELD_PATTERN: Final = re.compile(
    r"^\s+(?P<field>[a-z_]+)\s+required,",
    re.MULTILINE,
)


class SessionHarnessError(RuntimeError):
    """Report an invalid infrastructure observation or fixture contract."""


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
        """Create a handoff from generated input and the real CLI contract."""
        selected = payload if payload is not None else self.generated_payload()
        if work_branch is not None:
            module = load_verify_session_claims_module()
            selected = selected.with_field(module.SESSION_GIT_REF_FIELD, work_branch)
        return self._run(("handoff",), input_text=selected.wire_text())

    def generated_payload(self) -> HandoffPayload:
        """Generate input from fields the real CLI reports as required."""
        return generated_handoff_payload(self._required_handoff_fields())

    def generated_payload_batch(self) -> tuple[HandoffPayload, ...]:
        """Generate the source-declared multi-session scenario batch."""
        return generated_handoff_batch(self._required_handoff_fields())

    def _required_handoff_fields(self) -> tuple[str, ...]:
        """Read required JSON field names from the real CLI help contract."""
        help_result = self._run(("handoff", "--help"))
        if help_result.returncode != 0:
            raise SessionHarnessError(help_result.stderr)
        fields = tuple(HANDOFF_REQUIRED_FIELD_PATTERN.findall(help_result.stdout))
        if not fields:
            raise SessionHarnessError(
                "spx session handoff --help reported no required JSON fields"
            )
        return fields

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
    "current_branch",
    "session_commands",
]

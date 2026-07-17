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
    handoff_git_env,
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

    def created_session(
        self, result: subprocess.CompletedProcess[str]
    ) -> SessionRecord:
        """Resolve the emitted absolute session path and derive its identifier."""
        self.require_success(result)
        candidates = [
            Path(match.group("value"))
            for match in OUTPUT_MARKER_PATTERN.finditer(result.stdout)
            if Path(match.group("value")).is_absolute()
        ]
        if len(candidates) != 1:
            raise AssertionError(f"expected one emitted session path: {result.stdout}")
        path = candidates[0]
        return SessionRecord(session_id=path.stem, initial_path=path)

    def create_and_pickup(self, payload: HandoffPayload | None = None) -> SessionRecord:
        """Create one session, move it to the active queue, and return its record."""
        record = self.created_session(self.handoff(payload))
        self.require_success(self.pickup(record))
        return record

    def create_picked_up_batch(self) -> tuple[SessionRecord, ...]:
        """Create a multi-session batch from distinct whole-payload fixtures."""
        return tuple(
            self.create_and_pickup(payload)
            for payload in (basic_handoff_payload(), specific_content_handoff_payload())
        )

    def locate(self, record: SessionRecord) -> Path:
        """Locate one session by the filename the CLI emitted at creation."""
        matches = tuple(self.sessions_dir.rglob(record.initial_path.name))
        if len(matches) != 1:
            raise AssertionError(
                f"expected one current path for {record.session_id}: {matches}"
            )
        return matches[0]

    def session_files(self) -> tuple[Path, ...]:
        """Return every file the isolated session store contains."""
        return tuple(
            sorted(path for path in self.sessions_dir.rglob("*") if path.is_file())
        )

    def git_ref(self, record: SessionRecord) -> str | None:
        """Read the recorded git ref through the CLI's structured session API."""
        result = self._run(("show", "--json", record.session_id))
        self.require_success(result)
        payload = json.loads(result.stdout)
        if isinstance(payload, list):
            if len(payload) != 1 or not isinstance(payload[0], dict):
                raise TypeError("session show returned an unexpected record list")
            payload = payload[0]
        if not isinstance(payload, dict):
            raise TypeError("session show returned an unexpected record")
        module = load_verify_session_claims_module()
        value = payload.get(module.SESSION_GIT_REF_FIELD)
        return value if isinstance(value, str) else None

    @staticmethod
    def succeeded(result: subprocess.CompletedProcess[str]) -> bool:
        """Report whether a command completed successfully."""
        return result.returncode == 0

    @staticmethod
    def require_success(result: subprocess.CompletedProcess[str]) -> None:
        """Raise with the CLI diagnostic when a setup command fails."""
        if not SessionCommandHarness.succeeded(result):
            raise AssertionError(result.stderr)

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


def handoff_creates_session_file() -> bool:
    with accepted_session_commands() as commands:
        return commands.created_session(commands.handoff()).initial_path.exists()


def handoff_preserves_active_node() -> bool:
    payload = active_node_handoff_payload()
    with accepted_session_commands() as commands:
        record = commands.created_session(commands.handoff(payload))
        return payload.body in record.initial_path.read_text()


def handoff_records_current_branch() -> bool:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff())
        return commands.git_ref(record) == current_branch(repo)


def pickup_removes_initial_file() -> bool:
    with accepted_session_commands() as commands:
        record = commands.created_session(commands.handoff())
        result = commands.pickup(record)
        return commands.succeeded(result) and not record.initial_path.exists()


def pickup_moves_to_active_queue() -> bool:
    with accepted_session_commands() as commands:
        record = commands.created_session(commands.handoff())
        result = commands.pickup(record)
        return (
            commands.succeeded(result)
            and commands.locate(record).parent != record.initial_path.parent
        )


def pickup_emits_session_body() -> bool:
    payload = active_node_handoff_payload()
    with accepted_session_commands() as commands:
        record = commands.created_session(commands.handoff(payload))
        result = commands.pickup(record)
        return commands.succeeded(result) and payload.body in result.stdout


def release_removes_active_file() -> bool:
    with accepted_session_commands() as commands:
        record = commands.create_and_pickup()
        active_path = commands.locate(record)
        result = commands.release(record)
        return commands.succeeded(result) and not active_path.exists()


def release_returns_to_initial_queue() -> bool:
    with accepted_session_commands() as commands:
        record = commands.create_and_pickup()
        result = commands.release(record)
        return (
            commands.succeeded(result)
            and commands.locate(record).parent == record.initial_path.parent
        )


def release_preserves_content() -> bool:
    with accepted_session_commands() as commands:
        record = commands.create_and_pickup(specific_content_handoff_payload())
        content = commands.locate(record).read_text()
        result = commands.release(record)
        return (
            commands.succeeded(result)
            and commands.locate(record).read_text() == content
        )


def release_batch_returns_to_initial_queue() -> bool:
    with accepted_session_commands() as commands:
        records = commands.create_picked_up_batch()
        active_paths = tuple(commands.locate(record) for record in records)
        result = commands.release(*records)
        return (
            commands.succeeded(result)
            and all(not path.exists() for path in active_paths)
            and all(
                commands.locate(record).parent == record.initial_path.parent
                for record in records
            )
        )


def handoff_preserves_plan_content() -> bool:
    return _handoff_preserves_payload(plan_handoff_payload())


def handoff_preserves_issue_content() -> bool:
    return _handoff_preserves_payload(issues_handoff_payload())


def _handoff_preserves_payload(payload: HandoffPayload) -> bool:
    with accepted_session_commands() as commands:
        record = commands.created_session(commands.handoff(payload))
        return payload.body in record.initial_path.read_text()


def root_branch_handoff_records_branch() -> bool:
    with handoff_git_env() as env, session_commands(env.root) as commands:
        record = commands.created_session(commands.handoff())
        return commands.git_ref(record) == env.default_branch


def detached_root_handoff_records_head() -> bool:
    with handoff_git_env() as env:
        env.detach_root()
        with session_commands(env.root) as commands:
            record = commands.created_session(commands.handoff())
            return commands.git_ref(record) == env.head_sha()


def linked_tip_handoff_records_tip() -> bool:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            record = commands.created_session(commands.handoff())
            return commands.git_ref(record) == env.origin_tip


def linked_branch_handoff_is_refused() -> bool:
    with handoff_git_env() as env:
        with session_commands(env.linked_on_branch()) as commands:
            return _handoff_is_refused(commands)


def linked_off_tip_handoff_is_refused() -> bool:
    with handoff_git_env() as env:
        with session_commands(env.linked_detached_off_tip()) as commands:
            return _handoff_is_refused(commands)


def explicit_work_branch_is_recorded() -> bool:
    with handoff_git_env() as env:
        work_branch = env.push_work_branch()
        with session_commands(env.linked_at_origin_tip()) as commands:
            record = commands.created_session(commands.handoff(work_branch=work_branch))
            return commands.git_ref(record) == work_branch


def absent_work_branch_is_refused() -> bool:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            return _handoff_is_refused(commands, work_branch=env.head_sha())


def _handoff_is_refused(
    commands: SessionCommandHarness, *, work_branch: str | None = None
) -> bool:
    result = commands.handoff(work_branch=work_branch)
    return (
        not commands.succeeded(result)
        and bool(result.stderr)
        and not commands.session_files()
    )


@contextmanager
def accepted_session_commands() -> Iterator[SessionCommandHarness]:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        yield commands


__all__ = [
    "HandoffPayload",
    "SessionCommandHarness",
    "SessionRecord",
    "absent_work_branch_is_refused",
    "accepted_session_commands",
    "active_node_handoff_payload",
    "basic_handoff_payload",
    "current_branch",
    "detached_root_handoff_records_head",
    "explicit_work_branch_is_recorded",
    "handoff_creates_session_file",
    "handoff_preserves_active_node",
    "handoff_preserves_issue_content",
    "handoff_preserves_plan_content",
    "handoff_records_current_branch",
    "issues_handoff_payload",
    "linked_branch_handoff_is_refused",
    "linked_off_tip_handoff_is_refused",
    "linked_tip_handoff_records_tip",
    "plan_handoff_payload",
    "pickup_emits_session_body",
    "pickup_moves_to_active_queue",
    "pickup_removes_initial_file",
    "release_batch_returns_to_initial_queue",
    "release_preserves_content",
    "release_removes_active_file",
    "release_returns_to_initial_queue",
    "root_branch_handoff_records_branch",
    "session_commands",
    "specific_content_handoff_payload",
]

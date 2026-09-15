"""Read native child configuration and completion from a persisted thread."""

from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import IO, Final, Protocol, TypedDict
from pathlib import Path

from outcomeeng.distribution.installation import CommandResult
from outcomeeng.distribution.profiles import CodexConfiguration

THREAD_READ_COMMAND: Final = ("codex", "app-server", "--stdio", "--strict-config")
THREAD_READ_TIMEOUT_SECONDS: Final = 30.0
THREAD_READ_FAILED: Final = "native app-server thread/read failed"
_READ_CHUNK_BYTES: Final = 65536


class ChildIdentityField(StrEnum):
    """Identity fields supplied by the native thread/read response."""

    ID = "id"
    PARENT = "parentThreadId"
    ROLE = "agentRole"
    MODEL = "model"
    EFFORT = "reasoningEffort"


class NativeTurnStatus(StrEnum):
    """Turn states in the native app-server protocol."""

    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    IN_PROGRESS = "inProgress"


class NativeMessage(TypedDict):
    """Completion-message fields consumed from a native turn."""

    type: str
    text: str


class NativeTurn(TypedDict):
    """Turn fields needed to establish a completed native child."""

    status: NativeTurnStatus
    items: list[NativeMessage]
    error: object


class NativeChildThread(TypedDict):
    """Thread identity and turn evidence consumed from thread/read."""

    id: str
    parentThreadId: str | None
    agentRole: str | None
    model: str | None
    reasoningEffort: str | None
    turns: list[NativeTurn]


class NativeChildLookupPayload(TypedDict):
    """Native parent-filtered listing and child read observations."""

    childIds: list[str]
    thread: NativeChildThread


class NativeParentEvent(TypedDict):
    """Parent identity supplied by the exec JSONL stream."""

    type: str
    thread_id: str


NATIVE_MESSAGE_TYPE: Final = "agentMessage"
NATIVE_THREAD_STARTED: Final = "thread.started"
NATIVE_CHILD_SOURCE: Final = "subAgentThreadSpawn"


class NativeThreadReader(Protocol):
    """List and read the sole child of a parent in disposable state."""

    def __call__(
        self, thread_id: str, cwd: Path, environment: Mapping[str, str]
    ) -> CommandResult: ...


class NativeChildLookup(Protocol):
    """Native lookup boundary with explicit command and execution budget."""

    def __call__(
        self,
        parent_id: str,
        cwd: Path,
        environment: Mapping[str, str],
        *,
        timeout: float,
        command: Sequence[str],
    ) -> CommandResult: ...


@dataclass(frozen=True)
class NativeChildEvidence:
    """Native records and the first unavailable or inconsistent observation."""

    parent_id: str | None
    thread_read: CommandResult | None
    thread: Mapping[str, object] | None
    terminal_condition: str | None


def collect_native_child_evidence(
    stream: str,
    role: str,
    configuration: CodexConfiguration,
    *,
    reader: NativeThreadReader,
    cwd: Path,
    environment: Mapping[str, str],
) -> NativeChildEvidence:
    """Correlate a parent-filtered listing and native read without inference."""
    try:
        parent_id = _single_parent(stream)
    except ValueError as error:
        return NativeChildEvidence(None, None, None, str(error))
    result = reader(parent_id, cwd, environment)
    if result.exit_code != 0:
        return NativeChildEvidence(
            parent_id, result, None, "native child thread read failed"
        )
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError:
        return NativeChildEvidence(
            parent_id, result, None, "native child thread read is not JSON"
        )
    thread = document.get("thread") if isinstance(document, dict) else None
    if not isinstance(thread, dict):
        return NativeChildEvidence(
            parent_id, result, None, "native child thread is absent"
        )
    child_ids = document.get("childIds")
    if (
        not isinstance(child_ids, list)
        or len(child_ids) != 1
        or not isinstance(child_ids[0], str)
        or not child_ids[0]
        or child_ids[0] == parent_id
    ):
        return NativeChildEvidence(
            parent_id, result, thread, "native listing has no single child identity"
        )
    receiver_id = child_ids[0]
    expected = {
        ChildIdentityField.ID: receiver_id,
        ChildIdentityField.PARENT: parent_id,
        ChildIdentityField.ROLE: role,
        ChildIdentityField.MODEL: configuration.model,
        ChildIdentityField.EFFORT: configuration.model_reasoning_effort,
    }
    for field, value in expected.items():
        if thread.get(field) != value:
            return NativeChildEvidence(
                parent_id,
                result,
                thread,
                f"native child {field} is missing or mismatched",
            )
    condition = _completion_condition(thread)
    return NativeChildEvidence(parent_id, result, thread, condition)


def _single_parent(stream: str) -> str:
    parents: list[str] = []
    for line in stream.splitlines():
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("native parent stream contains a non-object event")
        if event.get("type") == NATIVE_THREAD_STARTED:
            parent_id = event.get("thread_id")
            if not isinstance(parent_id, str) or not parent_id:
                raise ValueError("native parent thread identity is absent")
            parents.append(parent_id)
    if len(parents) != 1:
        raise ValueError("native parent stream has no single thread identity")
    return parents[0]


def _completion_condition(thread: Mapping[str, object]) -> str | None:
    turns = thread.get("turns")
    if not isinstance(turns, list) or len(turns) != 1:
        return "native child does not contain exactly one turn"
    turn = turns[0]
    if (
        not isinstance(turn, dict)
        or turn.get("status") != NativeTurnStatus.COMPLETED
        or turn.get("error") is not None
    ):
        return "native child turn did not complete"
    items = turn.get("items")
    if isinstance(items, list) and any(
        isinstance(item, dict)
        and item.get("type") == NATIVE_MESSAGE_TYPE
        and isinstance(item.get("text"), str)
        and item["text"].strip()
        for item in items
    ):
        return None
    return "native child completion message is absent"


def _read_native_record(
    thread_id: str,
    cwd: Path,
    environment: Mapping[str, str],
    *,
    children: bool,
    timeout: float = THREAD_READ_TIMEOUT_SECONDS,
    command: Sequence[str] = THREAD_READ_COMMAND,
) -> CommandResult:
    """Own a bounded foreground app-server exchange and collect its process."""
    response: Mapping[str, object] = {}
    condition: str | None = None
    with tempfile.TemporaryFile() as stderr:
        try:
            with subprocess.Popen(
                command,
                cwd=cwd,
                env=dict(environment),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=stderr,
                start_new_session=True,
            ) as process:
                try:
                    if process.stdin is None or process.stdout is None:
                        raise OSError("native app-server pipes are unavailable")
                    deadline = time.monotonic() + timeout
                    exchange = _Exchange(process.stdin, process.stdout, deadline)
                    initialized = exchange.request(
                        0,
                        "initialize",
                        {
                            "clientInfo": {
                                "name": "native-profile-evidence",
                                "version": "1",
                            },
                            "capabilities": {"experimentalApi": True},
                        },
                    )
                    if "error" in initialized:
                        response = initialized
                        condition = "native app-server initialization failed"
                    else:
                        exchange.send({"method": "initialized"})
                        if children:
                            response = {"result": _read_child(exchange, thread_id)}
                        else:
                            response = exchange.request(
                                1,
                                "thread/read",
                                {"threadId": thread_id, "includeTurns": True},
                            )
                            if "error" in response:
                                condition = THREAD_READ_FAILED
                    process.stdin.close()
                    process.wait(timeout=max(0.0, deadline - time.monotonic()))
                    if process.returncode != 0:
                        condition = f"native app-server exited {process.returncode}"
                except (
                    OSError,
                    ValueError,
                    subprocess.TimeoutExpired,
                ) as error:
                    condition = str(error)
                finally:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
        except OSError as error:
            condition = str(error)
        stderr.seek(0)
        diagnostic = stderr.read().decode("utf-8", errors="replace")
    return CommandResult(
        tuple(command),
        int(condition is not None),
        json.dumps(response.get("result", response)),
        diagnostic + (f"\n{condition}" if condition is not None else ""),
    )


def read_native_thread(
    thread_id: str,
    cwd: Path,
    environment: Mapping[str, str],
    *,
    timeout: float = THREAD_READ_TIMEOUT_SECONDS,
    command: Sequence[str] = THREAD_READ_COMMAND,
) -> CommandResult:
    """Read a specific native thread without launching a model turn."""
    return _read_native_record(
        thread_id, cwd, environment, children=False, timeout=timeout, command=command
    )


def read_native_child(
    parent_id: str,
    cwd: Path,
    environment: Mapping[str, str],
    *,
    timeout: float = THREAD_READ_TIMEOUT_SECONDS,
    command: Sequence[str] = THREAD_READ_COMMAND,
) -> CommandResult:
    """List active and archived children, then read the sole child's turns."""
    return _read_native_record(
        parent_id, cwd, environment, children=True, timeout=timeout, command=command
    )


def _read_child(exchange: _Exchange, parent_id: str) -> Mapping[str, object]:
    pages: list[Mapping[str, object]] = []
    child_ids: list[str] = []
    for archived in (False, True):
        failure = _list_children(exchange, parent_id, archived, pages, child_ids)
        if failure is not None:
            return failure
    document: dict[str, object] = {"pages": pages, "childIds": child_ids}
    if len(child_ids) == 1:
        response = exchange.request(
            len(pages) + 1,
            "thread/read",
            {"threadId": child_ids[0], "includeTurns": True},
        )
        document["read"] = response
        result = response.get("result")
        if isinstance(result, dict):
            document["thread"] = result.get("thread")
    return document


def _list_children(
    exchange: _Exchange,
    parent_id: str,
    archived: bool,
    pages: list[Mapping[str, object]],
    child_ids: list[str],
) -> Mapping[str, object] | None:
    cursor: str | None = None
    seen: set[str] = set()
    while True:
        response = exchange.request(
            len(pages) + 1,
            "thread/list",
            {
                "parentThreadId": parent_id,
                "sourceKinds": [NATIVE_CHILD_SOURCE],
                "archived": archived,
                "cursor": cursor,
            },
        )
        pages.append(response)
        page = response.get("result")
        if (
            not isinstance(page, dict)
            or not isinstance(page.get("data"), list)
            or "nextCursor" not in page
        ):
            return {
                "pages": pages,
                "childIds": child_ids,
                "error": "native child listing failed",
            }
        if not _append_child_ids(page["data"], parent_id, child_ids):
            return {
                "pages": pages,
                "error": "native child listing identity is invalid",
            }
        cursor = page.get("nextCursor")
        if cursor is None:
            return None
        if not isinstance(cursor, str) or not cursor or cursor in seen:
            return {
                "pages": pages,
                "error": "native child listing cursor is invalid",
            }
        seen.add(cursor)


def _append_child_ids(
    children: list[object], parent_id: str, child_ids: list[str]
) -> bool:
    for child in children:
        if (
            not isinstance(child, dict)
            or child.get("parentThreadId") != parent_id
            or not isinstance(child.get("id"), str)
            or not child["id"]
        ):
            return False
        child_ids.append(child["id"])
    return True


@dataclass
class _Exchange:
    stdin: IO[bytes]
    stdout: IO[bytes]
    deadline: float
    pending: bytes = b""

    def send(self, document: Mapping[str, object]) -> None:
        self.stdin.write((json.dumps(document) + "\n").encode())
        self.stdin.flush()

    def request(
        self, identifier: int, method: str, parameters: Mapping[str, object]
    ) -> Mapping[str, object]:
        self.send({"id": identifier, "method": method, "params": parameters})
        with selectors.DefaultSelector() as selector:
            selector.register(self.stdout, selectors.EVENT_READ)
            while time.monotonic() < self.deadline:
                document = self._pending_response(identifier)
                if document is not None:
                    return document
                if not selector.select(max(0.0, self.deadline - time.monotonic())):
                    break
                chunk = os.read(self.stdout.fileno(), _READ_CHUNK_BYTES)
                if not chunk:
                    raise OSError("native app-server closed before responding")
                self.pending += chunk
        raise TimeoutError("native app-server read deadline exceeded")

    def _pending_response(self, identifier: int) -> Mapping[str, object] | None:
        while b"\n" in self.pending:
            line, self.pending = self.pending.split(b"\n", 1)
            document = json.loads(line)
            if isinstance(document, dict) and document.get("id") == identifier:
                if "result" not in document and "error" not in document:
                    raise ValueError(
                        "native app-server response has no result or error"
                    )
                return document
        return None

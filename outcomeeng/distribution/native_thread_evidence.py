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


class NativeThreadPayload(TypedDict):
    """Native thread/read result envelope."""

    thread: NativeChildThread


class NativeSpawnItem(TypedDict):
    """Exec JSONL collaboration fields used to correlate the receiver."""

    id: str
    type: str
    tool: str
    status: str
    sender_thread_id: str
    receiver_thread_ids: list[str]


class NativeParentEvent(TypedDict, total=False):
    """Exec JSONL fields consumed by the child-evidence collector."""

    type: str
    thread_id: str
    item: NativeSpawnItem


NATIVE_MESSAGE_TYPE: Final = "agentMessage"
NATIVE_COLLAB_TYPE: Final = "collab_tool_call"
NATIVE_SPAWN_TOOL: Final = "spawn_agent"
NATIVE_THREAD_STARTED: Final = "thread.started"
NATIVE_ITEM_STARTED: Final = "item.started"
NATIVE_ITEM_COMPLETED: Final = "item.completed"
NATIVE_SPAWN_COMPLETED: Final = "completed"


class NativeThreadReader(Protocol):
    """Read one persisted thread in the selected disposable environment."""

    def __call__(
        self, thread_id: str, cwd: Path, environment: Mapping[str, str]
    ) -> CommandResult: ...


@dataclass(frozen=True)
class NativeChildEvidence:
    """Native records and the first unavailable or inconsistent observation."""

    spawn: Mapping[str, object] | None
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
    """Correlate one spawn and one native read, without retry or inference."""
    try:
        parent_id, spawn = _single_spawn(stream)
    except ValueError as error:
        return NativeChildEvidence(None, None, None, str(error))
    receivers = spawn["receiver_thread_ids"]
    # _single_spawn validates this external field before it reaches the reader.
    if not isinstance(receivers, list) or len(receivers) != 1:
        return NativeChildEvidence(spawn, None, None, "spawn has no single receiver")
    receiver_id = receivers[0]
    result = reader(receiver_id, cwd, environment)
    if result.exit_code != 0:
        return NativeChildEvidence(
            spawn, result, None, "native child thread read failed"
        )
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError:
        return NativeChildEvidence(
            spawn, result, None, "native child thread read is not JSON"
        )
    thread = document.get("thread") if isinstance(document, dict) else None
    if not isinstance(thread, dict):
        return NativeChildEvidence(spawn, result, None, "native child thread is absent")
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
                spawn, result, thread, f"native child {field} is missing or mismatched"
            )
    condition = _completion_condition(thread)
    return NativeChildEvidence(spawn, result, thread, condition)


def _single_spawn(stream: str) -> tuple[str, dict[str, object]]:
    parents: list[str] = []
    starts: list[str] = []
    completions: list[dict[str, object]] = []
    for line in stream.splitlines():
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("native parent stream contains a non-object event")
        if event.get("type") == NATIVE_THREAD_STARTED:
            parent_id = event.get("thread_id")
            if not isinstance(parent_id, str) or not parent_id:
                raise ValueError("native parent thread identity is absent")
            parents.append(parent_id)
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != NATIVE_COLLAB_TYPE:
            continue
        if item.get("tool") != NATIVE_SPAWN_TOOL:
            continue
        if event.get("type") == NATIVE_ITEM_STARTED:
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                raise ValueError("native spawn call identity is absent")
            starts.append(item_id)
        elif event.get("type") == NATIVE_ITEM_COMPLETED:
            completions.append(item)
    if len(parents) != 1 or not isinstance(parents[0], str) or not parents[0]:
        raise ValueError("native parent stream has no single thread identity")
    if len(starts) != 1 or len(completions) != 1:
        raise ValueError("native parent stream has no single spawn lifecycle")
    spawn = completions[0]
    if not isinstance(starts[0], str) or not starts[0] or spawn.get("id") != starts[0]:
        raise ValueError("native spawn lifecycle identities do not match")
    receivers = spawn.get("receiver_thread_ids")
    if (
        spawn.get("status") != NATIVE_SPAWN_COMPLETED
        or spawn.get("sender_thread_id") != parents[0]
        or not isinstance(receivers, list)
        or len(receivers) != 1
        or not isinstance(receivers[0], str)
        or not receivers[0]
        or receivers[0] == parents[0]
    ):
        raise ValueError("native spawn does not identify one successful child")
    return parents[0], spawn


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


def read_native_thread(
    thread_id: str,
    cwd: Path,
    environment: Mapping[str, str],
    *,
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
                        response = exchange.request(
                            1,
                            "thread/read",
                            {
                                "threadId": thread_id,
                                "includeTurns": True,
                            },
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
                    TimeoutError,
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
                while b"\n" in self.pending:
                    line, self.pending = self.pending.split(b"\n", 1)
                    document = json.loads(line)
                    if isinstance(document, dict) and document.get("id") == identifier:
                        if "result" not in document and "error" not in document:
                            raise ValueError(
                                "native app-server response has no result or error"
                            )
                        return document
                if not selector.select(max(0.0, self.deadline - time.monotonic())):
                    break
                chunk = os.read(self.stdout.fileno(), _READ_CHUNK_BYTES)
                if not chunk:
                    raise OSError("native app-server closed before responding")
                self.pending += chunk
        raise TimeoutError("native app-server read deadline exceeded")

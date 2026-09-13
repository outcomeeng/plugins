"""Resource ownership and controlled native-read protocol observations."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final
from uuid import uuid4

from hypothesis import given, seed, settings

from outcomeeng.distribution.installation import CommandResult
from outcomeeng.distribution.native_thread_evidence import (
    THREAD_READ_COMMAND,
    ChildIdentityField,
    NativeChildEvidence,
    NativeChildThread,
    NativeThreadPayload,
    NativeTurnStatus,
    collect_native_child_evidence,
    read_native_thread,
)
from outcomeeng_testing.generators.native_thread_evidence import (
    NativeEvidenceCase,
    native_evidence_cases,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

_EVIDENCE_SEED: Final = 20260912
_EVIDENCE_REPLAY: Final = (
    "just test spx/32-distribution.enabler/21-installation.enabler/"
    "21-repository-installation.enabler/tests/test_native_profile_execution.compliance.l1.py"
)


@dataclass
class RecordingThreadReader:
    """Stage 5 failure simulation and interaction protocols; no verdict logic."""

    response: CommandResult
    calls: list[tuple[str, Path, Mapping[str, str]]] = field(default_factory=list)

    def __call__(
        self, thread_id: str, cwd: Path, environment: Mapping[str, str]
    ) -> CommandResult:
        self.calls.append((thread_id, cwd, dict(environment)))
        return self.response

    @classmethod
    def from_thread(cls, thread: NativeChildThread) -> RecordingThreadReader:
        return cls(
            CommandResult(
                THREAD_READ_COMMAND,
                0,
                json.dumps(NativeThreadPayload(thread=thread)),
                "",
            )
        )

    @classmethod
    def without_identity(
        cls, thread: NativeChildThread, identity: ChildIdentityField
    ) -> RecordingThreadReader:
        document: dict[str, object] = dict(thread)
        del document[identity]
        return cls(
            CommandResult(THREAD_READ_COMMAND, 0, json.dumps({"thread": document}), "")
        )

    @classmethod
    def mismatched_identity(
        cls, thread: NativeChildThread, identity: ChildIdentityField
    ) -> RecordingThreadReader:
        document: dict[str, object] = dict(thread)
        document[identity] = str(document[identity]) + str(uuid4())
        return cls(
            CommandResult(THREAD_READ_COMMAND, 0, json.dumps({"thread": document}), "")
        )

    @classmethod
    def failed_read(cls) -> RecordingThreadReader:
        return cls(CommandResult(THREAD_READ_COMMAND, 1, "", "native read unavailable"))

    @classmethod
    def with_turn_status(
        cls, thread: NativeChildThread, status: NativeTurnStatus
    ) -> RecordingThreadReader:
        document = json.loads(json.dumps(NativeThreadPayload(thread=thread)))
        document["thread"]["turns"][0]["status"] = status
        return cls(CommandResult(THREAD_READ_COMMAND, 0, json.dumps(document), ""))

    @classmethod
    def without_turns(cls, thread: NativeChildThread) -> RecordingThreadReader:
        document = json.loads(json.dumps(NativeThreadPayload(thread=thread)))
        document["thread"]["turns"] = []
        return cls(CommandResult(THREAD_READ_COMMAND, 0, json.dumps(document), ""))

    @classmethod
    def without_completion_message(
        cls, thread: NativeChildThread
    ) -> RecordingThreadReader:
        document = json.loads(json.dumps(NativeThreadPayload(thread=thread)))
        document["thread"]["turns"][0]["items"] = []
        return cls(CommandResult(THREAD_READ_COMMAND, 0, json.dumps(document), ""))

    @classmethod
    def without_thread(cls) -> RecordingThreadReader:
        return cls(CommandResult(THREAD_READ_COMMAND, 0, "{}", ""))


@dataclass(frozen=True)
class NativeEvidenceContext:
    cwd: Path
    environment: Mapping[str, str]

    def collect(
        self, case: NativeEvidenceCase, reader: RecordingThreadReader
    ) -> NativeChildEvidence:
        return collect_native_child_evidence(
            case.stream,
            case.role,
            case.configuration,
            reader=reader,
            cwd=self.cwd,
            environment=self.environment,
        )


def exercise_native_evidence(
    assert_case: Callable[[NativeEvidenceCase, NativeEvidenceContext], None],
) -> None:
    """Own generated-run policy and resources; leave all predicates to tests."""
    with TemporaryDirectory(prefix="native-child-evidence-") as temporary:
        context = NativeEvidenceContext(Path(temporary), {})

        @seed(_EVIDENCE_SEED)
        @settings(print_blob=True)
        @given(case=native_evidence_cases())
        def run_cases(case: NativeEvidenceCase) -> None:
            assert_case(case, context)

        run_replayable_property(
            run_cases, seed_value=_EVIDENCE_SEED, replay_path=_EVIDENCE_REPLAY
        )


def read_absent_native_thread() -> CommandResult:
    """Exercise the real app-server read in empty state without a model turn."""
    with TemporaryDirectory(prefix="native-thread-read-") as temporary:
        root = Path(temporary)
        (root / "codex").mkdir()
        (root / "sqlite").mkdir()
        environment = {
            "PATH": os.environ["PATH"],
            "HOME": temporary,
            "CODEX_HOME": str(root / "codex"),
            "CODEX_SQLITE_HOME": str(root / "sqlite"),
        }
        return read_native_thread(str(uuid4()), root, environment)

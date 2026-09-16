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

from outcomeeng.distribution.installation import (
    CommandResult,
    HOME_ENV,
    CODEX_HOME_ENV,
    CODEX_SQLITE_HOME_ENV,
)
from outcomeeng.distribution.native_thread_evidence import (
    THREAD_READ_COMMAND,
    ChildIdentityField,
    NativeChildEvidence,
    NativeChildThread,
    NativeChildLookupPayload,
    NativeTurnStatus,
    NativeEvidenceField,
    collect_native_child_evidence,
    read_native_thread,
    read_native_child,
)
from outcomeeng_testing.generators.native_thread_evidence import (
    NativeEvidenceCase,
    native_evidence_cases,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

_EVIDENCE_SEED: Final = 20260912
_EVIDENCE_REPLAY: Final = (
    "just test spx/32-distribution.enabler/21-installation.enabler/"
    "32-native-subagent-execution.enabler/tests/test_native_profile_execution.compliance.l1.py"
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
                json.dumps(
                    NativeChildLookupPayload(
                        childIds=[thread[ChildIdentityField.ID.value]], thread=thread
                    )
                ),
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
            CommandResult(
                THREAD_READ_COMMAND,
                0,
                json.dumps(
                    {
                        NativeEvidenceField.CHILD_IDS: [
                            thread[ChildIdentityField.ID.value]
                        ],
                        NativeEvidenceField.THREAD: document,
                    }
                ),
                "",
            )
        )

    @classmethod
    def mismatched_identity(
        cls, thread: NativeChildThread, identity: ChildIdentityField
    ) -> RecordingThreadReader:
        document: dict[str, object] = dict(thread)
        document[identity] = str(document[identity]) + str(uuid4())
        return cls(
            CommandResult(
                THREAD_READ_COMMAND,
                0,
                json.dumps(
                    {
                        NativeEvidenceField.CHILD_IDS: [
                            thread[ChildIdentityField.ID.value]
                        ],
                        NativeEvidenceField.THREAD: document,
                    }
                ),
                "",
            )
        )

    @classmethod
    def failed_read(cls) -> RecordingThreadReader:
        return cls(CommandResult(THREAD_READ_COMMAND, 1, "", "native read unavailable"))

    @classmethod
    def with_turn_status(
        cls, thread: NativeChildThread, status: NativeTurnStatus
    ) -> RecordingThreadReader:
        document = json.loads(
            json.dumps(
                NativeChildLookupPayload(
                    childIds=[thread[ChildIdentityField.ID.value]], thread=thread
                )
            )
        )
        document[NativeEvidenceField.THREAD][NativeEvidenceField.TURNS][0][
            NativeEvidenceField.STATUS
        ] = status
        return cls(CommandResult(THREAD_READ_COMMAND, 0, json.dumps(document), ""))

    @classmethod
    def without_turns(cls, thread: NativeChildThread) -> RecordingThreadReader:
        document = json.loads(
            json.dumps(
                NativeChildLookupPayload(
                    childIds=[thread[ChildIdentityField.ID.value]], thread=thread
                )
            )
        )
        document[NativeEvidenceField.THREAD][NativeEvidenceField.TURNS] = []
        return cls(CommandResult(THREAD_READ_COMMAND, 0, json.dumps(document), ""))

    @classmethod
    def without_completion_message(
        cls, thread: NativeChildThread
    ) -> RecordingThreadReader:
        document = json.loads(
            json.dumps(
                NativeChildLookupPayload(
                    childIds=[thread[ChildIdentityField.ID.value]], thread=thread
                )
            )
        )
        document[NativeEvidenceField.THREAD][NativeEvidenceField.TURNS][0][
            NativeEvidenceField.ITEMS
        ] = []
        return cls(CommandResult(THREAD_READ_COMMAND, 0, json.dumps(document), ""))

    @classmethod
    def with_extra_child(cls, thread: NativeChildThread) -> RecordingThreadReader:
        document = NativeChildLookupPayload(
            childIds=[thread[ChildIdentityField.ID.value], str(uuid4())], thread=thread
        )
        return cls(CommandResult(THREAD_READ_COMMAND, 0, json.dumps(document), ""))

    @classmethod
    def without_listed_child(cls, thread: NativeChildThread) -> RecordingThreadReader:
        document = NativeChildLookupPayload(childIds=[], thread=thread)
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


def _read_empty_native_state(*, children: bool) -> CommandResult:
    """Exercise the real app-server read in empty state without a model turn."""
    with TemporaryDirectory(prefix="native-thread-read-") as temporary:
        root = Path(temporary)
        (root / "codex").mkdir()
        (root / "sqlite").mkdir()
        environment = {
            "PATH": os.environ["PATH"],
            HOME_ENV: temporary,
            CODEX_HOME_ENV: str(root / "codex"),
            CODEX_SQLITE_HOME_ENV: str(root / "sqlite"),
        }
        reader = read_native_child if children else read_native_thread
        return reader(str(uuid4()), root, environment)


def read_absent_native_thread() -> CommandResult:
    """Read an unknown thread through the real app-server without a model turn."""
    return _read_empty_native_state(children=False)


def read_absent_native_child() -> CommandResult:
    """Exercise real parent-filtered active and archived child listing."""
    return _read_empty_native_state(children=True)

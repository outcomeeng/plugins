"""Recording doubles for the sync orchestrator.

Implements the `StepRunner`, `ToolProbe`, and `ChangeProbe` Protocols
declared in `outcomeeng.distribution.sync`. The doubles are spies
(recording calls) and stubs (returning scripted results), used by `l1`
tests to verify sync's orchestration without invoking real subprocesses
or mutating marketplace state.

Exception cases per `plugins/spec-tree/skills/test/references/methodology.md`:
- Stage 5 #2 (Interaction protocols): sync's correctness depends on the
  sequence and presence of step calls.
- Stage 5 #4 (Safety): real sync mutates the marketplace cache and shells
  out to network-bound tooling.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from outcomeeng.distribution.sync import ChangeProbe, StepRunner, ToolProbe


@dataclass
class RecordingRunner:
    """StepRunner that returns scripted exit codes in order of call.

    `exit_codes` drives the i-th call's return value (default 0 once exhausted).
    `calls` records the argv tuple of each call in order.
    """

    exit_codes: Sequence[int] = ()
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, argv: Sequence[str]) -> int:
        index = len(self.calls)
        self.calls.append(tuple(argv))
        if index < len(self.exit_codes):
            return self.exit_codes[index]
        return 0


@dataclass
class ScriptedToolProbe:
    """ToolProbe that returns True only for tools in `available`."""

    available: frozenset[str]
    queries: list[str] = field(default_factory=list)

    def __call__(self, name: str) -> bool:
        self.queries.append(name)
        return name in self.available


@dataclass
class ScriptedChangeProbe:
    """ChangeProbe that returns `changed` for every query."""

    changed: bool
    queries: list[str] = field(default_factory=list)

    def __call__(self, base_ref: str) -> bool:
        self.queries.append(base_ref)
        return self.changed


__all__ = ["RecordingRunner", "ScriptedChangeProbe", "ScriptedToolProbe"]


_: type[StepRunner] = RecordingRunner
_2: type[ToolProbe] = ScriptedToolProbe
_3: type[ChangeProbe] = ScriptedChangeProbe

"""Recording double for the clean orchestrator.

Implements the `Runner` Protocol declared in `outcomeeng.hygiene.clean`.
The double is a spy (recording calls) and a stub (returning a scripted
exit code), used by `l1` tests to verify clean's argv contract without
invoking real `git clean -fdX` against the test machine.

Exception case per `plugins/spec-tree/skills/test/references/methodology.md`:
- Stage 5 #2 (Interaction protocols): clean's correctness is the argv it
  passes to `git`.
- Stage 5 #4 (Safety): real `git clean -fdX` mutates the test machine's
  working tree.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from outcomeeng.hygiene.clean import Runner


@dataclass
class RecordingRunner:
    """Runner that returns a scripted exit code and records every call."""

    exit_code: int = 0
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, argv: Sequence[str]) -> int:
        self.calls.append(tuple(argv))
        return self.exit_code


__all__ = ["RecordingRunner"]


_: type[Runner] = RecordingRunner

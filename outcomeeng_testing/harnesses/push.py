"""Recording doubles for the push orchestrator.

Reuses `RecordingRunner` and `ScriptedToolProbe` from
`outcomeeng_testing.harnesses.sync` (the protocol shapes are identical
across the two orchestrators). Adds `ScriptedUpstreamProbe` for push's
upstream-ref capture step.

Exception case per `plugins/spec-tree/skills/test/references/methodology.md`:
- Stage 5 #2 (Interaction protocols): push's correctness depends on the
  presence and ordering of git/upstream/sync calls.
- Stage 5 #4 (Safety): real push mutates origin and triggers marketplace
  refresh.
"""

from __future__ import annotations

from dataclasses import dataclass

from outcomeeng.distribution.push import UpstreamProbe


@dataclass
class ScriptedUpstreamProbe:
    """UpstreamProbe that returns a scripted ref (or None) on each call."""

    ref: str | None
    calls: int = 0

    def __call__(self) -> str | None:
        self.calls += 1
        return self.ref


__all__ = ["ScriptedUpstreamProbe"]


_: type[UpstreamProbe] = ScriptedUpstreamProbe

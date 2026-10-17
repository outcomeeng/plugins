"""Configuration and measurement domains for usage-controller evidence.

The values mirror the node spec's declared defaults and bounds. They are test
inputs, not production defaults; the controller reads them from its configuration
file.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

PASS_INTERVAL_MINUTES = 30
PACE_TOKENS = 1_000
COMPACTION_CONTEXT_PERCENT = 30
COMPACTION_MULTIPLE = 1.25
PAUSE_MULTIPLE = 2
WEEKLY_CEILING_PERCENT = 93
CEILING_MAXIMUM_PERCENT = 95
LOW_WEEKLY_PERCENT = 40
LOW_CONTEXT_PERCENT = 5

ALPHA = "alpha"
BETA = "beta"


class AgentKind(StrEnum):
    CLAUDE = "claude"
    CODEX = "codex"


@dataclass(frozen=True)
class PositionSpec:
    """One configured position and the Prowl pane that hosts it."""

    ordinal: int
    subscription: str
    kind: AgentKind = AgentKind.CLAUDE
    in_prowl: bool = True

    @property
    def worktree(self) -> str:
        return f"/work/positions/position-{self.ordinal}"

    @property
    def pane(self) -> str:
        return f"pane-{self.ordinal}"

    @property
    def title(self) -> str:
        return f"Position {self.ordinal}"


def alpha_positions(count: int) -> tuple[PositionSpec, ...]:
    return tuple(PositionSpec(ordinal, ALPHA) for ordinal in range(1, count + 1))


def share(pace: int, measured_positions: int) -> float:
    """A position's share: the subscription's pace divided evenly."""
    return pace / measured_positions


def tokens_above(share_tokens: float, multiple: float) -> int:
    """The smallest whole token count strictly above `multiple` times the share."""
    return int(share_tokens * multiple) + 1


def tokens_at_most(share_tokens: float, multiple: float) -> int:
    """The largest whole token count not above `multiple` times the share."""
    return int(share_tokens * multiple)


def tokens_under(share_tokens: float) -> int:
    """A whole token count strictly under the share."""
    return int(share_tokens) - 1


def ceiling_accepted_values() -> tuple[int, ...]:
    """Ceilings at or below the maximum the controller accepts."""
    return (WEEKLY_CEILING_PERCENT, CEILING_MAXIMUM_PERCENT)


def ceiling_rejected_values() -> tuple[float, ...]:
    """Ceilings strictly above the maximum, from the smallest step to the extreme."""
    return (CEILING_MAXIMUM_PERCENT + 0.01, CEILING_MAXIMUM_PERCENT + 1, 100, 250)

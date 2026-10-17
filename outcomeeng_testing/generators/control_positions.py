"""Configuration and measurement domains for usage-controller evidence.

The values mirror the node spec's declared defaults and bounds. They are test
inputs, not production defaults; the controller reads them from its configuration
file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

SECONDS_PER_MINUTE = 60
PASS_BOUND_MINUTES = 5
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


def non_finite_values() -> tuple[float, ...]:
    """The IEEE non-finite members a TOML float literal can spell: nan, inf, -inf."""
    return (math.nan, math.inf, -math.inf)


def ceiling_rejected_values() -> tuple[float, ...]:
    """Ceilings outside the accepted range: strictly above the maximum, from the
    smallest step to the extreme, and the non-finite members a TOML float can spell
    that no comparison against the maximum catches."""
    return (
        CEILING_MAXIMUM_PERCENT + 0.01,
        CEILING_MAXIMUM_PERCENT + 1,
        100,
        250,
        math.nan,
        math.inf,
    )


TOKEN_MEASUREMENT_DEADLINES = 2  # the sibling's collect and measure each carry one


def token_reserve_shortfalls(reserve_seconds: float) -> tuple[float, ...]:
    """Seconds left before the pass bound that fall short of the reserve.

    Each member is positive and strictly below `reserve_seconds`, so the longest
    token measurement cannot finish inside it; binary fractions keep the clock
    arithmetic exact.
    """
    return (
        reserve_seconds - 0.125,
        reserve_seconds - 1,
        reserve_seconds / 2,
        1.0,
    )


class SiblingApiChange(StrEnum):
    """One way a sibling release can change the accounting API the controller reads."""

    MEASURE_RETURNS_LIST = "measure returns a list"
    MEASURE_RETURNS_NUMBER = "measure returns a number"
    MEASURE_RETURNS_NONE = "measure returns nothing"
    WORKSPACES_NOT_MAPPING = "workspaces are not a mapping"
    GROUP_MISSING_KEY = "workspace group lacks a token key"
    GROUP_NOT_MAPPING = "workspace group is not a mapping"
    CONFIG_CONSTRUCTOR_REMOVED = "config constructor removed"
    DEFAULT_PROJECTS_REMOVED = "default projects attribute removed"
    EVIDENCE_REMOVED = "evidence class removed"
    MEASURE_REMOVED = "measure removed"


def sibling_api_changes() -> tuple[SiblingApiChange, ...]:
    """Every sibling API change the degrade-to-unmeasured claim covers."""
    return tuple(SiblingApiChange)


def just_before_pass_bound(command_timeout_seconds: float) -> tuple[float, ...]:
    """Elapsed seconds at which a command can start with the pass bound still ahead.

    The members are the boundary starts between the bound minus two command timeouts
    and the bound itself; binary fractions keep the clock arithmetic exact.
    """
    bound = PASS_BOUND_MINUTES * SECONDS_PER_MINUTE
    return (
        bound - 0.125,
        bound - 1,
        bound - command_timeout_seconds / 2,
        bound - command_timeout_seconds,
        bound - command_timeout_seconds - 1,
    )

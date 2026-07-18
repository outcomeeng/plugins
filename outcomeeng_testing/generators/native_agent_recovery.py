"""Generated public-Prowl domains for native-agent recovery evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

MIN_RECOVERY_PANES = 1
MAX_RECOVERY_PANES = 21


@dataclass(frozen=True)
class RecoveryRosterShape:
    pane_count: int
    correlated_count: int


@dataclass(frozen=True)
class RecoveryRosterCase:
    pane_ids: tuple[str, ...]
    worktree_paths: tuple[Path, ...]
    correlated_count: int
    unknown_pane_id: str
    non_native_occupied_count: int

    @property
    def correlated_pane_ids(self) -> tuple[str, ...]:
        return self.pane_ids[: self.correlated_count]

    @property
    def unoccupied_pane_ids(self) -> tuple[str, ...]:
        return self.pane_ids[self.correlated_count :]

    @property
    def duplicate_selection(self) -> tuple[str, ...]:
        return (self.pane_ids[0], self.pane_ids[0])


OPERATIONAL_RECOVERY_SHAPE = RecoveryRosterShape(
    pane_count=MAX_RECOVERY_PANES,
    correlated_count=2,
)


def recovery_roster_case(
    shape: RecoveryRosterShape,
    namespace: str,
) -> RecoveryRosterCase:
    root = Path("/") / namespace
    pane_ids = tuple(
        f"11111111-1111-4111-8111-{index:012d}" for index in range(shape.pane_count)
    )
    worktree_paths = tuple(
        root / f"worktree-{index}" for index in range(shape.pane_count)
    )
    return RecoveryRosterCase(
        pane_ids=pane_ids,
        worktree_paths=worktree_paths,
        correlated_count=shape.correlated_count,
        unknown_pane_id="99999999-9999-4999-8999-999999999999",
        non_native_occupied_count=1,
    )


OPERATIONAL_RECOVERY_ROSTER = recovery_roster_case(
    OPERATIONAL_RECOVERY_SHAPE,
    "restart-recovery-evidence",
)


@st.composite
def recovery_roster_cases(draw: st.DrawFn) -> RecoveryRosterCase:
    pane_count = draw(
        st.integers(
            min_value=MIN_RECOVERY_PANES,
            max_value=MAX_RECOVERY_PANES,
        )
    )
    correlated_count = draw(st.integers(min_value=0, max_value=pane_count))
    namespace = draw(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=16,
        )
    )
    return recovery_roster_case(
        RecoveryRosterShape(
            pane_count=pane_count,
            correlated_count=correlated_count,
        ),
        namespace,
    )


def roster_cases() -> SearchStrategy[RecoveryRosterCase]:
    return recovery_roster_cases()


def non_native_agent_types(
    native_agent_types: frozenset[str],
) -> SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=16,
    ).filter(lambda agent_type: agent_type not in native_agent_types)

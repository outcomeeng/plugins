"""Generated public-Prowl domains for native-agent recovery evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

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
    session_ids: tuple[str, ...]
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
    session_ids = tuple(
        f"22222222-2222-4222-8222-{index:012d}" for index in range(shape.pane_count)
    )
    return RecoveryRosterCase(
        pane_ids=pane_ids,
        worktree_paths=worktree_paths,
        session_ids=session_ids,
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


def recovery_candidates(
    module: ModuleType,
    roster: RecoveryRosterCase,
) -> list[dict[str, object]]:
    return [
        {
            module.PANE_ID_FIELD: pane_id,
            module.WORKTREE_PATH_FIELD: str(worktree),
            module.SESSION_ID_FIELD: session_id,
            module.EVIDENCE_FIELD: module.EvidenceKind.LIVE_PROCESS,
            module.ROLE_FIELD: module.RecoveryRole.PRIMARY,
            module.SECONDARY_AUTHORIZED_FIELD: False,
        }
        for pane_id, worktree, session_id in zip(
            roster.pane_ids,
            roster.worktree_paths,
            roster.session_ids,
            strict=True,
        )
    ]


def recovery_delivery_results(
    module: ModuleType,
    pane_ids: tuple[str, ...],
    *,
    failed_pane_id: str | None = None,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for pane_id in pane_ids:
        if pane_id == failed_pane_id:
            transport = {
                module.SCHEMA_VERSION_FIELD: module.TRANSPORT_SCHEMA_VERSION,
                module.OPERATION_FIELD: module.TRANSPORT_SEND_OPERATION,
                module.STATUS_FIELD: module.TRANSPORT_COMMAND_FAILED_STATUS,
                module.DETAIL_FIELD: f"delivery failed for {pane_id}",
                module.COMMAND_EXIT_CODE_FIELD: MAX_RECOVERY_PANES,
            }
        else:
            transport = {
                module.SCHEMA_VERSION_FIELD: module.TRANSPORT_SCHEMA_VERSION,
                module.OPERATION_FIELD: module.TRANSPORT_SEND_OPERATION,
                module.STATUS_FIELD: module.TRANSPORT_SUCCEEDED_STATUS,
                module.COMMAND_EXIT_CODE_FIELD: 0,
                module.RESPONSE_FIELD: {},
            }
        results.append(
            {
                module.PANE_ID_FIELD: pane_id,
                module.TRANSPORT_FIELD: transport,
            }
        )
    return results


def invalid_recovery_evidence(
    evidence_kinds: tuple[str, ...],
) -> SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=16,
    ).filter(lambda evidence: evidence not in evidence_kinds)


def non_native_agent_types(
    native_agent_types: frozenset[str],
) -> SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=16,
    ).filter(lambda agent_type: agent_type not in native_agent_types)

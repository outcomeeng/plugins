"""Generated domains for two-phase native-agent recovery evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

MIN_RECOVERY_PANES = 1
MAX_RECOVERY_PANES = 23


@dataclass(frozen=True)
class RecoveryRosterShape:
    pane_count: int
    correlated_count: int


@dataclass(frozen=True)
class RecoveryRosterCase:
    original_pane_ids: tuple[str, ...]
    post_restart_pane_ids: tuple[str, ...]
    worktree_paths: tuple[Path, ...]
    session_ids: tuple[str, ...]
    agent_types: tuple[str, ...]
    correlated_count: int
    unknown_pane_id: str

    @property
    def correlated_post_restart_pane_ids(self) -> tuple[str, ...]:
        return self.post_restart_pane_ids[: self.correlated_count]


OPERATIONAL_RECOVERY_SHAPE = RecoveryRosterShape(
    pane_count=MAX_RECOVERY_PANES,
    correlated_count=2,
)


def recovery_roster_case(
    shape: RecoveryRosterShape,
    namespace: str,
) -> RecoveryRosterCase:
    root = Path("/") / namespace
    agent_types = ("claude", "codex", "pi")
    return RecoveryRosterCase(
        original_pane_ids=tuple(
            f"11111111-1111-4111-8111-{index:012d}" for index in range(shape.pane_count)
        ),
        post_restart_pane_ids=tuple(
            f"33333333-3333-4333-8333-{index:012d}" for index in range(shape.pane_count)
        ),
        worktree_paths=tuple(
            root / f"worktree-{index}" for index in range(shape.pane_count)
        ),
        session_ids=tuple(
            f"22222222-2222-4222-8222-{index:012d}" for index in range(shape.pane_count)
        ),
        agent_types=tuple(
            agent_types[index % len(agent_types)] for index in range(shape.pane_count)
        ),
        correlated_count=shape.correlated_count,
        unknown_pane_id="99999999-9999-4999-8999-999999999999",
    )


OPERATIONAL_RECOVERY_ROSTER = recovery_roster_case(
    OPERATIONAL_RECOVERY_SHAPE,
    "restart-recovery-evidence",
)


@st.composite
def recovery_roster_cases(draw: st.DrawFn) -> RecoveryRosterCase:
    pane_count = draw(
        st.integers(min_value=MIN_RECOVERY_PANES, max_value=MAX_RECOVERY_PANES)
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
    sources = tuple(module.EvidenceSource)
    return [
        {
            module.PANE_ID_FIELD: pane_id,
            module.WORKTREE_PATH_FIELD: str(worktree),
            module.SESSION_ID_FIELD: session_id,
            module.RESUME_LOCATOR_FIELD: session_id,
            module.NATIVE_HOME_FIELD: None,
            module.AGENT_TYPE_FIELD: agent_type,
            module.EVIDENCE_FIELD: sources[index % len(sources)],
            module.ROLE_FIELD: module.RecoveryRole.PRIMARY,
            module.SECONDARY_AUTHORIZED_FIELD: False,
        }
        for index, (pane_id, worktree, session_id, agent_type) in enumerate(
            zip(
                roster.original_pane_ids,
                roster.worktree_paths,
                roster.session_ids,
                roster.agent_types,
                strict=True,
            )
        )
    ]


def identity_evidence(
    module: ModuleType,
    roster: RecoveryRosterCase,
    pane_ids: tuple[str, ...],
) -> list[dict[str, object]]:
    sources = tuple(module.EvidenceSource)
    return [
        {
            module.PANE_ID_FIELD: pane_id,
            module.WORKTREE_PATH_FIELD: str(worktree),
            module.SESSION_ID_FIELD: session_id,
            module.AGENT_TYPE_FIELD: agent_type,
            module.SOURCE_FIELD: sources[index % len(sources)],
        }
        for index, (pane_id, worktree, session_id, agent_type) in enumerate(
            zip(
                pane_ids,
                roster.worktree_paths,
                roster.session_ids,
                roster.agent_types,
                strict=True,
            )
        )
    ]


def activation_results(
    module: ModuleType,
    activations: list[dict[str, object]],
    pane_ids: tuple[str, ...],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for action, pane_id in zip(activations, pane_ids, strict=True):
        operation = action[module.OPERATION_FIELD]
        worktree_path = action[module.WORKTREE_PATH_FIELD]
        results.append(
            {
                module.ORIGINAL_PANE_ID_FIELD: action[module.ORIGINAL_PANE_ID_FIELD],
                module.TRANSPORT_FIELD: {
                    module.SCHEMA_VERSION_FIELD: module.TRANSPORT_SCHEMA_VERSION,
                    module.OPERATION_FIELD: operation,
                    module.STATUS_FIELD: module.TRANSPORT_SUCCEEDED_STATUS,
                    module.COMMAND_EXIT_CODE_FIELD: 0,
                    module.RESPONSE_FIELD: {
                        "ok": True,
                        "data": {
                            "target": {
                                "pane": {"id": pane_id},
                                "worktree": {
                                    "id": worktree_path,
                                    "path": worktree_path,
                                    "root_path": str(Path(str(worktree_path)).parent),
                                },
                            }
                        },
                    },
                },
            }
        )
    return results


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

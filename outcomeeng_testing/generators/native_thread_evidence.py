"""Variable native protocol inputs for child-evidence boundary tests."""

import json
from dataclasses import dataclass

from hypothesis import strategies as st

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.native_thread_evidence import (
    NATIVE_COLLAB_TYPE,
    NATIVE_ITEM_COMPLETED,
    NATIVE_ITEM_STARTED,
    NATIVE_MESSAGE_TYPE,
    NATIVE_SPAWN_COMPLETED,
    NATIVE_SPAWN_TOOL,
    NATIVE_THREAD_STARTED,
    NativeChildThread,
    NativeMessage,
    NativeParentEvent,
    NativeSpawnItem,
    NativeTurn,
    NativeTurnStatus,
)
from outcomeeng.distribution.profiles import AGENT_PROFILES, CodexConfiguration


@dataclass(frozen=True)
class NativeEvidenceCase:
    """Correlated protocol documents constructed independently of the parser."""

    role: str
    configuration: CodexConfiguration
    events: tuple[NativeParentEvent, ...]
    thread: NativeChildThread

    @property
    def stream(self) -> str:
        return "\n".join(json.dumps(event) for event in self.events)


@st.composite
def native_evidence_cases(draw: st.DrawFn) -> NativeEvidenceCase:
    """Vary profile, parent/child/call identities, role, and returned text."""
    configuration = draw(st.sampled_from(tuple(AGENT_PROFILES[Target.CODEX].values())))
    if not isinstance(configuration, CodexConfiguration):
        raise TypeError("central configuration is not native to the selected harness")
    parent, child, call = draw(
        st.lists(st.uuids(), min_size=3, max_size=3, unique=True)
    )
    role = str(draw(st.uuids()))
    message = draw(st.text(min_size=1).filter(lambda value: bool(value.strip())))
    spawn = NativeSpawnItem(
        id=str(call),
        type=NATIVE_COLLAB_TYPE,
        tool=NATIVE_SPAWN_TOOL,
        status=NATIVE_SPAWN_COMPLETED,
        sender_thread_id=str(parent),
        receiver_thread_ids=[str(child)],
    )
    return NativeEvidenceCase(
        role,
        configuration,
        (
            NativeParentEvent(type=NATIVE_THREAD_STARTED, thread_id=str(parent)),
            NativeParentEvent(type=NATIVE_ITEM_STARTED, item=spawn),
            NativeParentEvent(type=NATIVE_ITEM_COMPLETED, item=spawn),
        ),
        NativeChildThread(
            id=str(child),
            parentThreadId=str(parent),
            agentRole=role,
            model=configuration.model,
            reasoningEffort=configuration.model_reasoning_effort,
            turns=[
                NativeTurn(
                    status=NativeTurnStatus.COMPLETED,
                    error=None,
                    items=[NativeMessage(type=NATIVE_MESSAGE_TYPE, text=message)],
                )
            ],
        ),
    )

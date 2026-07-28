"""Source-owned agent-hook event and payload contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Final

SESSION_START_EVENT: Final = "SessionStart"
SESSION_ID_FIELD: Final = "session_id"
CURRENT_WORKING_DIRECTORY_FIELD: Final = "cwd"


def session_start_payload(
    *, session_id: str | None, current_working_directory: Path
) -> dict[str, object]:
    """Return one SessionStart payload using the agent-hook field contract."""
    payload: dict[str, object] = {
        CURRENT_WORKING_DIRECTORY_FIELD: str(current_working_directory)
    }
    if session_id is not None:
        payload[SESSION_ID_FIELD] = session_id
    return payload


__all__ = [
    "CURRENT_WORKING_DIRECTORY_FIELD",
    "SESSION_ID_FIELD",
    "SESSION_START_EVENT",
    "session_start_payload",
]

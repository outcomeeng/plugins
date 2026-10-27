"""Source-owned agent-hook event and payload contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Final

SESSION_START_EVENT: Final = "SessionStart"
MATCHER_FIELD: Final = "matcher"
# The empty matcher selects every SessionStart source; the compact matcher selects
# only the source that follows a compaction.
SESSION_START_EVERY_SOURCE_MATCHER: Final = ""
SESSION_START_COMPACT_MATCHER: Final = "compact"
# The environment variable the harness substitutes with the plugin's install root,
# and the shell expansion that names it inside a hook command.
PLUGIN_ROOT_ENV: Final = "CLAUDE_PLUGIN_ROOT"
PLUGIN_ROOT_TOKEN: Final = f"${{{PLUGIN_ROOT_ENV}}}"
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
    "MATCHER_FIELD",
    "PLUGIN_ROOT_ENV",
    "PLUGIN_ROOT_TOKEN",
    "SESSION_START_COMPACT_MATCHER",
    "SESSION_START_EVERY_SOURCE_MATCHER",
    "SESSION_ID_FIELD",
    "SESSION_START_EVENT",
    "session_start_payload",
]

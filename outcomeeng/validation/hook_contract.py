"""Source-owned agent-hook event and payload contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Final

SESSION_START_EVENT: Final = "SessionStart"
PRE_TOOL_USE_EVENT: Final = "PreToolUse"
SESSION_ID_FIELD: Final = "session_id"
CURRENT_WORKING_DIRECTORY_FIELD: Final = "cwd"

# The one shipped hook permitted on a blocking-capable event: the spec-tree plugin's
# pre-write check, a PreToolUse entry whose matcher names exactly the Write and Edit
# tools and whose command runs the write-boundary adapter.
PRE_WRITE_PLUGIN: Final = "spec-tree"
PRE_WRITE_TOOLS: Final[frozenset[str]] = frozenset({"Write", "Edit"})
PRE_WRITE_MATCHER_SEPARATOR: Final = "|"
PRE_WRITE_ADAPTER_SCRIPT: Final = "scripts/write_boundary.py"
PRE_WRITE_ADAPTER_INTERPRETER: Final = "python3"
PRE_WRITE_KILL_SWITCH: Final = "SPECTREE_WRITE_BOUNDARY_HOOK_DISABLED"
PRE_WRITE_EMPTY_RESULT: Final = "{}"
CLAUDE_PLUGIN_ROOT_TOKEN: Final = "${CLAUDE_PLUGIN_ROOT}"
CODEX_PLUGIN_ROOT_TOKEN: Final = "${PLUGIN_ROOT}"
# The build rewrites ${CLAUDE_SKILL_DIR} to ${SKILL_DIR} in the dist/codex tree.
CLAUDE_SKILL_DIR_TOKEN: Final = "${CLAUDE_SKILL_DIR}"
CODEX_SKILL_DIR_TOKEN: Final = "${SKILL_DIR}"
SUBSTITUTED_PATH_TOKENS: Final[tuple[str, ...]] = (
    CLAUDE_PLUGIN_ROOT_TOKEN,
    CLAUDE_SKILL_DIR_TOKEN,
    CODEX_PLUGIN_ROOT_TOKEN,
    CODEX_SKILL_DIR_TOKEN,
)

# The generated runtime trees a hook config ships under, and where a plugin keeps it.
CLAUDE_RUNTIME_TREE: Final = "dist/claude"
CODEX_RUNTIME_TREE: Final = "dist/codex"
RUNTIME_TREES: Final[tuple[str, ...]] = (CLAUDE_RUNTIME_TREE, CODEX_RUNTIME_TREE)
HOOKS_DIRECTORY: Final = "hooks"
HOOKS_CONFIG_FILE: Final = "hooks.json"

# The hooks.json schema keys the validator reads.
HOOKS_KEY: Final = "hooks"
MATCHER_KEY: Final = "matcher"
COMMAND_KEY: Final = "command"
TIMEOUT_KEY: Final = "timeout"

# Report wording that identifies an event-level violation.
BLOCKING_EVENT_VIOLATION_MARKER: Final = "hook on blocking-capable event"


def _pre_write_command(plugin_root_token: str) -> str:
    """Return the pre-write check's inline-guarded command for one runtime tree."""
    empty = f"echo '{PRE_WRITE_EMPTY_RESULT}'"
    adapter = f"{PRE_WRITE_ADAPTER_INTERPRETER} {plugin_root_token}/{PRE_WRITE_ADAPTER_SCRIPT}"
    return (
        f'if [ "${{{PRE_WRITE_KILL_SWITCH}:-}}" = "1" ]; then {empty}; '
        f"else command -v {PRE_WRITE_ADAPTER_INTERPRETER} >/dev/null 2>&1 && {adapter} || {empty}; fi"
    )


# The pre-write check's exact command in the dist/claude tree and in the dist/codex
# tree, where the build rewrites ${CLAUDE_PLUGIN_ROOT} to ${PLUGIN_ROOT}.
PRE_WRITE_COMMAND_CLAUDE: Final = _pre_write_command(CLAUDE_PLUGIN_ROOT_TOKEN)
PRE_WRITE_COMMAND_CODEX: Final = _pre_write_command(CODEX_PLUGIN_ROOT_TOKEN)
PRE_WRITE_COMMANDS: Final[frozenset[str]] = frozenset(
    {PRE_WRITE_COMMAND_CLAUDE, PRE_WRITE_COMMAND_CODEX}
)


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
    "BLOCKING_EVENT_VIOLATION_MARKER",
    "CLAUDE_PLUGIN_ROOT_TOKEN",
    "CLAUDE_RUNTIME_TREE",
    "CLAUDE_SKILL_DIR_TOKEN",
    "CODEX_PLUGIN_ROOT_TOKEN",
    "CODEX_RUNTIME_TREE",
    "CODEX_SKILL_DIR_TOKEN",
    "COMMAND_KEY",
    "HOOKS_CONFIG_FILE",
    "HOOKS_DIRECTORY",
    "HOOKS_KEY",
    "MATCHER_KEY",
    "RUNTIME_TREES",
    "SUBSTITUTED_PATH_TOKENS",
    "TIMEOUT_KEY",
    "PRE_WRITE_COMMANDS",
    "PRE_WRITE_COMMAND_CLAUDE",
    "PRE_WRITE_COMMAND_CODEX",
    "PRE_WRITE_EMPTY_RESULT",
    "PRE_WRITE_KILL_SWITCH",
    "PRE_TOOL_USE_EVENT",
    "PRE_WRITE_ADAPTER_INTERPRETER",
    "PRE_WRITE_ADAPTER_SCRIPT",
    "PRE_WRITE_MATCHER_SEPARATOR",
    "PRE_WRITE_PLUGIN",
    "PRE_WRITE_TOOLS",
    "CURRENT_WORKING_DIRECTORY_FIELD",
    "SESSION_ID_FIELD",
    "SESSION_START_EVENT",
    "session_start_payload",
]

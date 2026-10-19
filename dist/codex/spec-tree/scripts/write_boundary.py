#!/usr/bin/env python3
"""Bound the destination of a Claude Code Write or Edit call to the granted roots.

Runs as the spec-tree plugin's ``PreToolUse`` hook adapter. Reads the hook payload on
standard input, the harness environment, and the Claude Code settings files that apply
to the project directory; runs no subprocess. Prints one JSON result and exits zero:
``{}`` allows the call, a ``permissionDecision`` of ``deny`` rejects it. Every failure
allows the call, so only a destination this check resolves outside every granted root
is denied.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import PurePath
from typing import Final

WRITE_TOOLS: Final = frozenset({"Write", "Edit"})
PROJECT_DIR_ENV: Final = "CLAUDE_PROJECT_DIR"
CONFIG_DIR_ENV: Final = "CLAUDE_CONFIG_DIR"
TEMP_BASE_ENV: Final = "CLAUDE_CODE_TMPDIR"
MACOS_PLATFORM: Final = "darwin"
LINUX_PLATFORM: Final = "linux"
MACOS_TEMP_BASE: Final = "/tmp"  # harness-documented base
TEMP_ROOT_PREFIX: Final = "claude-"
SCRATCH_DIRECTORY: Final = "scratchpad"
DEFAULT_CONFIG_DIR: Final = "~/.claude"
USER_SETTINGS_FILE: Final = "settings.json"
PROJECT_SETTINGS_DIR: Final = ".claude"
PROJECT_SETTINGS_FILES: Final = ("settings.json", "settings.local.json")
TOOL_NAME_FIELD: Final = "tool_name"
TOOL_INPUT_FIELD: Final = "tool_input"
FILE_PATH_FIELD: Final = "file_path"
SESSION_ID_FIELD: Final = "session_id"
TRANSCRIPT_PATH_FIELD: Final = "transcript_path"
CWD_FIELD: Final = "cwd"
PERMISSIONS_KEY: Final = "permissions"
ADDITIONAL_DIRECTORIES_KEY: Final = "additionalDirectories"
SETTINGS_ENCODING: Final = "utf-8"
EVENT_NAME: Final = "PreToolUse"
HOOK_SPECIFIC_OUTPUT_FIELD: Final = "hookSpecificOutput"
HOOK_EVENT_NAME_FIELD: Final = "hookEventName"
PERMISSION_DECISION_FIELD: Final = "permissionDecision"
PERMISSION_DECISION_REASON_FIELD: Final = "permissionDecisionReason"
DENY_DECISION: Final = "deny"
ALLOW_RESULT: Final = "{}"


def resolve(path: str, base: str) -> PurePath:
    """Resolve ``path`` against ``base`` through the symbolic links of its existing ancestors."""
    return PurePath(os.path.realpath(os.path.join(base, os.path.expanduser(path))))


def inside(path: PurePath, root: PurePath) -> bool:
    """Return whether ``path`` equals ``root`` or lies below it, by whole case-sensitive components."""
    return path.parts[: len(root.parts)] == root.parts


def additional_directories(settings_file: str) -> list[str]:
    """Return the ``permissions.additionalDirectories`` entries of one settings file."""
    try:
        with open(settings_file, encoding=SETTINGS_ENCODING) as handle:
            settings = json.load(handle)
    except FileNotFoundError:
        return []
    if not isinstance(settings, dict):
        raise ValueError(settings_file)
    permissions = settings.get(PERMISSIONS_KEY)
    if permissions is None:
        return []
    if not isinstance(permissions, dict):
        raise ValueError(settings_file)
    entries = permissions.get(ADDITIONAL_DIRECTORIES_KEY)
    if entries is None:
        return []
    if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
        raise ValueError(settings_file)
    return entries


def temp_root() -> PurePath:
    """Return the harness's temporary root, the per-user directory holding every session scratch.

    The base is ``CLAUDE_CODE_TMPDIR`` when set and non-empty, else ``/tmp`` on macOS and the
    process temporary directory on Linux. Any other platform raises, so the caller allows the call.
    """
    base = os.environ.get(TEMP_BASE_ENV)
    if not base:
        if sys.platform == MACOS_PLATFORM:
            base = MACOS_TEMP_BASE
        elif sys.platform.startswith(LINUX_PLATFORM):
            base = tempfile.gettempdir()
        else:
            raise ValueError(sys.platform)
    return resolve(f"{TEMP_ROOT_PREFIX}{os.getuid()}", base)


def scratch_directory(payload: dict[str, object], root: PurePath) -> PurePath:
    """Return the payload session's scratch directory under the temporary root."""
    session_id = payload.get(SESSION_ID_FIELD)
    transcript = payload.get(TRANSCRIPT_PATH_FIELD)
    if not isinstance(session_id, str) or not session_id:
        raise ValueError(SESSION_ID_FIELD)
    if not isinstance(transcript, str) or not transcript:
        raise ValueError(TRANSCRIPT_PATH_FIELD)
    project_key = PurePath(transcript).parent.name
    if not project_key:
        raise ValueError(TRANSCRIPT_PATH_FIELD)
    return root / project_key / session_id / SCRATCH_DIRECTORY


def judge(payload: dict[str, object], environment: dict[str, str]) -> str | None:
    """Return a denial reason for the payload's destination, or ``None`` to allow."""
    tool = payload.get(TOOL_NAME_FIELD)
    if tool is not None and tool not in WRITE_TOOLS:
        return None
    tool_input = payload.get(TOOL_INPUT_FIELD)
    if not isinstance(tool_input, dict):
        return None
    destination = tool_input.get(FILE_PATH_FIELD)
    if not isinstance(destination, str) or not destination:
        return None
    project_dir = environment.get(PROJECT_DIR_ENV)
    if not project_dir:
        return None
    project = resolve(project_dir, os.getcwd())
    cwd = payload.get(CWD_FIELD)
    base = cwd if isinstance(cwd, str) and cwd else str(project)
    target = resolve(destination, base)
    root = temp_root()
    scratch = scratch_directory(payload, root)
    config = resolve(
        environment.get(CONFIG_DIR_ENV) or DEFAULT_CONFIG_DIR, str(project)
    )
    settings_files = [str(config / USER_SETTINGS_FILE)] + [
        str(project / PROJECT_SETTINGS_DIR / name) for name in PROJECT_SETTINGS_FILES
    ]
    additional = [
        resolve(entry, str(project))
        for settings_file in settings_files
        for entry in additional_directories(settings_file)
    ]
    # Inside the temporary root only the session's scratch directory is granted, so an
    # additional directory admits a destination only outside that root.
    if inside(target, root):
        admitting = [project, config, scratch]
    else:
        admitting = [project, config, scratch, *additional]
    if any(inside(target, granted) for granted in admitting):
        return None
    granted_roots = ", ".join(
        str(granted)
        for granted in dict.fromkeys([project, scratch, config, *additional])
    )
    return (
        f"Write boundary: {destination} resolves to {target}, outside the granted roots "
        f"({granted_roots}). Write inside a granted root."
    )


def main() -> int:
    """Print the hook result for the payload on standard input; always exit zero."""
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("payload")
        reason = judge(payload, dict(os.environ))
        if reason is None:
            result = ALLOW_RESULT
        else:
            result = json.dumps(
                {
                    HOOK_SPECIFIC_OUTPUT_FIELD: {
                        HOOK_EVENT_NAME_FIELD: EVENT_NAME,
                        PERMISSION_DECISION_FIELD: DENY_DECISION,
                        PERMISSION_DECISION_REASON_FIELD: reason,
                    }
                }
            )
    except Exception:
        result = ALLOW_RESULT
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())

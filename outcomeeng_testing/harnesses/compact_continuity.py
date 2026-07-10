"""Harnesses for compact-continuity configuration evidence."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"
COMPACT_PROMPT_FIELD = "compactPrompt"


def compact_prompt_is_undefined() -> bool:
    with CLAUDE_SETTINGS_PATH.open(encoding="utf-8") as settings_file:
        settings = json.load(settings_file)
    return COMPACT_PROMPT_FIELD not in settings

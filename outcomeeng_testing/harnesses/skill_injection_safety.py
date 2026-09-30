"""Skill-file scaffolding for skill-injection-safety evidence.

Each function writes or builds an input and returns it. The predicate that
decides pass or fail belongs to the linked test.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.skill_injection_safety import (
    INLINE_INJECTION_END,
    INLINE_INJECTION_START,
    SKILL_FILENAME,
)


def write_skill(directory: Path, *, body: str, name: str = SKILL_FILENAME) -> Path:
    """Write ``body`` as a skill file named ``name`` under ``directory``."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def inline_injection(command: str) -> str:
    """Return the inline execution-time injection span that runs ``command``."""
    return f"{INLINE_INJECTION_START}{command}{INLINE_INJECTION_END}"

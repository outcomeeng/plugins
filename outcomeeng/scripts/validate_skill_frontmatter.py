"""Validate SKILL.md frontmatter fields.

Delegates to the vendored ``quick_validate.py`` from ``anthropics/skills``
(Apache 2.0) for Agent Skills open-standard validation.  Claude Code-specific
fields that the open standard does not recognize are accepted via a curated
allowlist maintained here.

Usage::

    uv run python -m outcomeeng.scripts.validate_skill_frontmatter [SKILL.md ...]

Exit codes:
    0 - All files valid (or no SKILL.md files in args)
    1 - One or more files have invalid frontmatter fields
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from outcomeeng.vendor.anthropics_skills.quick_validate import (
    validate_skill as _default_validate_skill,
)

# Type for the vendored validator: (skill_dir) -> (valid, message)
type SkillValidator = Callable[[Path], tuple[bool, str]]

# Claude Code-specific fields accepted by the CLI but absent from the Agent
# Skills open standard.  Maintain this set as new CC fields appear in the
# marketplace's own skills.
CLAUDE_CODE_FIELDS: frozenset[str] = frozenset(
    {
        "argument-hint",
        "arguments",
        "disable-model-invocation",
        "user-invocable",
        "context",
        "when-to-use",
        "hooks",
        "agent",
        "model",
        "effort",
        "shell",
        "version",
        "paths",
    }
)


def validate_file(
    path: Path,
    *,
    validator: SkillValidator = _default_validate_skill,
) -> list[str]:
    """Validate a single SKILL.md file. Returns list of error messages."""
    skill_dir = path.parent
    valid, message = validator(skill_dir)

    if valid:
        return []

    # If the vendored script reports unexpected keys, check whether they
    # are all Claude Code-specific.  If so, the file is acceptable.
    if message.startswith("Unexpected key(s) in SKILL.md frontmatter:"):
        # Parse the unexpected keys from the message.
        # Format: "Unexpected key(s) in SKILL.md frontmatter: a, b. Allowed ..."
        keys_part = message.split(":")[1].split(".")[0].strip()
        unexpected = {k.strip() for k in keys_part.split(",")}
        truly_unknown = unexpected - CLAUDE_CODE_FIELDS
        if not truly_unknown:
            return []
        return [
            f"{path}: unknown frontmatter field(s): {', '.join(sorted(truly_unknown))}",
        ]

    return [f"{path}: {message}"]


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    skill_files = [
        Path(arg)
        for arg in args
        if Path(arg).name.lower() == "skill.md" and Path(arg).is_file()
    ]

    if not skill_files:
        return 0

    all_errors: list[str] = []
    for path in skill_files:
        all_errors.extend(validate_file(path))

    for error in all_errors:
        print(f"error: {error}", file=sys.stderr)

    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

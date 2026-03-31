"""Validate SKILL.md frontmatter fields against Claude Code's known fields.

Uses two complementary sources to build the valid field set:

1. **Binary extraction** — Parses the installed Claude Code CLI binary's
   embedded JavaScript to find frontmatter property access patterns.

2. **Skill descriptor extraction** — Finds the skill constructor call in
   the binary (anchored by "skillName:") and maps its camelCase properties
   back to YAML kebab-case field names.

The Agent Skills open standard fields serve as a minimum floor that is
always valid regardless of extraction success.

Usage::

    uv run python -m outcomeeng.scripts.validate_skill_frontmatter [SKILL.md ...]

Exit codes:
    0 - All files valid (or no SKILL.md files in args)
    1 - One or more files have invalid frontmatter fields
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

# Agent Skills open standard (agentskills.io/specification) — always valid.
STANDARD_FIELDS = frozenset(
    {
        "name",
        "description",
        "license",
        "compatibility",
        "metadata",
        "allowed-tools",
    }
)

# Map from camelCase JS property names (in the skill constructor) to their
# YAML frontmatter equivalents.
_CAMEL_TO_YAML: dict[str, str] = {
    "allowedTools": "allowed-tools",
    "argumentHint": "argument-hint",
    "argumentNames": "arguments",
    "disableModelInvocation": "disable-model-invocation",
    "userInvocable": "user-invocable",
    "executionContext": "context",
    "whenToUse": "when-to-use",
    "hooks": "hooks",
    "agent": "agent",
    "model": "model",
    "effort": "effort",
    "shell": "shell",
    "version": "version",
    "paths": "paths",
}

# Pattern to find frontmatter parsing sections in the binary's JS.
FRONTMATTER_SECTION_RE = re.compile(
    r"""\{frontmatter:([a-zA-Z_$][a-zA-Z0-9_$]*),"""
    r"""content:[a-zA-Z_$][a-zA-Z0-9_$]*\}"""
)

# YAML frontmatter block in markdown.
FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(.*?\n)---\s*\n",
    re.DOTALL,
)

# Simple YAML key extraction (top-level keys only).
YAML_KEY_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:", re.MULTILINE)


def find_claude_binary() -> Path | None:
    """Find the Claude Code CLI binary."""
    claude = shutil.which("claude")
    if not claude:
        return None
    p = Path(claude)
    try:
        p = p.resolve()
    except OSError:
        pass
    return p if p.is_file() else None


def extract_fields_from_binary(binary: Path) -> frozenset[str] | None:
    """Extract known SKILL.md frontmatter fields from the Claude binary."""
    try:
        result = subprocess.run(
            ["strings", str(binary)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    output = result.stdout
    fields: set[str] = set()

    # Strategy 1: Bracket-notation frontmatter property access.
    for match in FRONTMATTER_SECTION_RE.finditer(output):
        var = re.escape(match.group(1))
        start = match.start()
        end = min(start + 2000, len(output))
        section = output[start:end]

        for m in re.finditer(rf'{var}\["([a-zA-Z_][a-zA-Z0-9_-]*)"\]', section):
            fields.add(m.group(1))

    # Strategy 2: Skill descriptor constructor properties.
    for line in output.split("\n"):
        if "skillName:" not in line:
            continue
        for camel, yaml_name in _CAMEL_TO_YAML.items():
            if camel + ":" in line:
                fields.add(yaml_name)

    return frozenset(fields) if fields else None


def get_valid_fields(
    binary_finder: Callable[[], Path | None] = find_claude_binary,
    field_extractor: Callable[
        [Path], frozenset[str] | None
    ] = extract_fields_from_binary,
) -> frozenset[str]:
    """Get the set of valid SKILL.md frontmatter fields."""
    binary = binary_finder()
    if binary:
        extracted = field_extractor(binary)
        if extracted:
            return STANDARD_FIELDS | extracted

    print(
        "warning: Could not extract fields from Claude binary, "
        "using Agent Skills standard fields only",
        file=sys.stderr,
    )
    return STANDARD_FIELDS


def parse_frontmatter_keys(path: Path) -> list[str] | None:
    """Extract top-level YAML frontmatter keys from a SKILL.md file."""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    match = FRONTMATTER_RE.match(content)
    if not match:
        return None

    yaml_block = match.group(1)
    return YAML_KEY_RE.findall(yaml_block)


def validate_file(path: Path, valid_fields: frozenset[str]) -> list[str]:
    """Validate a single SKILL.md file. Returns list of error messages."""
    keys = parse_frontmatter_keys(path)
    if keys is None:
        return []

    errors = []
    for key in keys:
        if key not in valid_fields:
            errors.append(
                f"{path}: unknown frontmatter field '{key}'. "
                f"Valid fields: {', '.join(sorted(valid_fields))}"
            )
    return errors


def main(
    argv: list[str] | None = None,
    *,
    valid_fields: frozenset[str] | None = None,
) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if valid_fields is None:
        valid_fields = get_valid_fields()

    skill_files = [
        Path(arg)
        for arg in args
        if Path(arg).name.lower() == "skill.md" and Path(arg).is_file()
    ]

    if not skill_files:
        return 0

    all_errors: list[str] = []
    for path in skill_files:
        all_errors.extend(validate_file(path, valid_fields))

    for error in all_errors:
        print(f"error: {error}", file=sys.stderr)

    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate SKILL.md frontmatter fields against Claude Code's known fields.

Uses two complementary sources to build the valid field set:

1. **Binary extraction** — Parses the installed Claude Code CLI binary's
   embedded JavaScript to find frontmatter property access patterns.
   This catches fields accessed via `var["field"]` or `var.field`.

2. **Skill descriptor extraction** — Finds the skill constructor call in
   the binary (anchored by "skillName:") and maps its camelCase properties
   back to YAML kebab-case field names. This catches fields like `hooks`
   that are accessed indirectly via helper functions.

The Agent Skills open standard fields serve as a minimum floor that is
always valid regardless of extraction success.

Usage:
    python3 scripts/validate-skill-frontmatter.py [SKILL.md ...]

Exit codes:
    0 - All files valid (or no SKILL.md files in args)
    1 - One or more files have invalid frontmatter fields
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
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
# YAML frontmatter equivalents. Built from the Claude Code source:
#   CF7({skillName, displayName, description, allowedTools, argumentHint,
#         argumentNames, whenToUse, version, model, disableModelInvocation,
#         userInvocable, hooks, executionContext, agent, paths, effort, shell, ...})
# Only properties that correspond to user-facing YAML fields are included.
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
    """Extract known SKILL.md frontmatter fields from the Claude binary.

    Two extraction strategies:

    1. **Direct access** — Find {frontmatter:VAR,content:VAR} sections and
       extract VAR["field"] and VAR.field patterns. Catches fields like
       `allowed-tools`, `user-invocable`, `disable-model-invocation`.

    2. **Skill descriptor** — Find lines containing "skillName:" and check
       which known constructor properties are present. Maps camelCase
       property names back to YAML field names via _CAMEL_TO_YAML.
       Catches fields like `hooks` that are accessed indirectly.
    """
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
    # Only bracket notation (var["field-name"]) is reliable — it uses
    # string literals that are unambiguous YAML field names.
    # Dot notation (var.field) is too noisy because the frontmatter
    # variable is reused for other purposes in nearby code.
    for match in FRONTMATTER_SECTION_RE.finditer(output):
        var = re.escape(match.group(1))
        start = match.start()
        end = min(start + 2000, len(output))
        section = output[start:end]

        for m in re.finditer(rf'{var}\["([a-zA-Z_][a-zA-Z0-9_-]*)"\]', section):
            fields.add(m.group(1))

    # Strategy 2: Skill descriptor constructor properties.
    # Find lines with "skillName:" and check for known constructor
    # property names, mapping them from camelCase to YAML kebab-case.
    for line in output.split("\n"):
        if "skillName:" not in line:
            continue
        for camel, yaml_name in _CAMEL_TO_YAML.items():
            if camel + ":" in line:
                fields.add(yaml_name)

    return frozenset(fields) if fields else None


def get_valid_fields() -> frozenset[str]:
    """Get the set of valid SKILL.md frontmatter fields.

    Tries to extract from the Claude binary first, falls back to
    the Agent Skills standard if extraction fails.
    """
    binary = find_claude_binary()
    if binary:
        extracted = extract_fields_from_binary(binary)
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


def main() -> int:
    valid_fields = get_valid_fields()

    skill_files = [
        Path(arg)
        for arg in sys.argv[1:]
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

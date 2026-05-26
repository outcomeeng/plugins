#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import re
import sys
from pathlib import Path


FRONTMATTER_FOLDING_MARKERS = {">", ">-", "|", "|-"}


def _frontmatter_field(frontmatter: str, field_name: str) -> str | None:
    """Return a simple scalar or folded block field from YAML frontmatter."""
    lines = frontmatter.splitlines()
    prefix = f"{field_name}:"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue

        raw_value = line.split(":", 1)[1].strip()
        if raw_value not in FRONTMATTER_FOLDING_MARKERS:
            return raw_value.strip("\"'")

        block_lines: list[str] = []
        for block_line in lines[index + 1 :]:
            if block_line and not block_line.startswith((" ", "\t")):
                break
            if block_line.strip():
                block_lines.append(block_line.strip())
        return "\n".join(block_lines)

    return None


def validate_skill(skill_path: str | Path) -> tuple[bool, str]:
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter = match.group(1)

    # Check required fields
    name = _frontmatter_field(frontmatter, "name")
    if name is None:
        return False, "Missing 'name' in frontmatter"
    description = _frontmatter_field(frontmatter, "description")
    if description is None:
        return False, "Missing 'description' in frontmatter"

    # Check naming convention (hyphen-case: lowercase with hyphens)
    if not re.match(r"^[a-z0-9-]+$", name):
        return (
            False,
            f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)",
        )
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return (
            False,
            f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens",
        )

    # Check for angle brackets in actual description text, not YAML fold markers.
    if "<" in description or ">" in description:
        return False, "Description cannot contain angle brackets (< or >)"

    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)

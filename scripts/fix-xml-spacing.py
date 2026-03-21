#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

LIST_ITEM_RE = re.compile(
    r"""^
\s*
(?:
  [-*+]                  # bullet
  (?:\s+\[[xX]\])?       # optional task checkbox
  |
  \d+[.)]                # ordered list
)
\s+\S
""",
    re.VERBOSE,
)

CLOSING_TAG_RE = re.compile(r"^\s*(</[A-Za-z0-9_-]+>)\s*$")
FENCE_START_RE = re.compile(r"^\s*(```+|~~~+)")
FENCE_END_RE = re.compile(r"^\s*({fence})\s*$")


def get_newline(line: str) -> str:
    """Extract newline style from line."""
    return "\r\n" if line.endswith("\r\n") else "\n"


def needs_blank_line_before_tag(output_lines: list[str]) -> bool:
    """Check if a blank line is needed before the closing tag."""
    if not output_lines:
        return False

    prev = output_lines[-1]
    if not LIST_ITEM_RE.match(prev.rstrip("\n")):
        return False
    if prev.strip() == "":
        return False

    # Check if there's already a blank line
    has_blank = len(output_lines) >= 2 and output_lines[-1].strip() == ""
    return not has_blank


def process_fence_marker(
    line: str, in_fence: bool, fence: str | None
) -> tuple[bool, str | None, re.Pattern[str] | None]:
    """Process code fence markers and return updated fence state."""
    m = FENCE_START_RE.match(line)
    if not m:
        return in_fence, fence, None

    marker = m.group(1)
    if not in_fence:
        # Opening fence
        fence_end_re = re.compile(FENCE_END_RE.pattern.format(fence=re.escape(marker)))
        return True, marker, fence_end_re

    # Potentially closing fence - check if it matches
    assert fence is not None, "fence must be set when in_fence is True"
    fence_end_re = re.compile(FENCE_END_RE.pattern.format(fence=re.escape(fence)))
    if fence_end_re.match(line):
        return False, None, None

    return in_fence, fence, None


def process_closing_tag(line: str, output_lines: list[str]) -> tuple[bool, str | None]:
    """Process closing XML tag and return (should_skip_default_append, modified_line)."""
    m_close = CLOSING_TAG_RE.match(line)
    if not m_close or not output_lines:
        return False, None

    if needs_blank_line_before_tag(output_lines):
        output_lines.append(get_newline(line))

    # Unindent the closing tag
    tag = m_close.group(1)
    return True, tag + get_newline(line)


def fix_file(path: Path) -> bool:
    """Fix XML tag spacing in markdown file. Returns True if file was modified."""
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(True)  # keep newlines

    out: list[str] = []
    in_fence = False
    fence = None

    for line in lines:
        # Track fence state
        new_fence, new_fence_marker, _ = process_fence_marker(line, in_fence, fence)
        if new_fence != in_fence or new_fence_marker != fence:
            in_fence = new_fence
            fence = new_fence_marker
            out.append(line)
            continue

        # Process closing tags outside fences
        if not in_fence:
            should_skip, modified_line = process_closing_tag(line, out)
            if should_skip:
                assert modified_line is not None
                out.append(modified_line)
                continue

        out.append(line)

    updated = "".join(out)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed_any = False
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_file():
            changed_any |= fix_file(p)
    return 1 if changed_any else 0


if __name__ == "__main__":
    raise SystemExit(main())

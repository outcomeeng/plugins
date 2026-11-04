"""Derive the level views of a document written from the PDR or spec template form.

A document in that form holds a title, an opening, subsection headings, rules
opened by a slug, and mapping tables. Level 1 is the path, the title, and the
opening. Level 2 adds each heading, each rule's slug and sentence, and the first
column of each mapping table. Level 3 is the whole file.

Usage: python3 "${SKILL_DIR}/scripts/document_levels.py" --level 1|2|3 <file>

A file without a title line prints an error naming the expected form and exits 1;
an unreadable file prints the operating-system error and exits 1.

Tested with a PDR and a spec document in template form at each of the three
levels. The script reads one file, writes nothing, and leaves nothing to clean up.
"""

from __future__ import annotations

import argparse
import sys
from enum import IntEnum
from pathlib import Path

FRONT_MATTER_FENCE = "---"
TITLE_PREFIX = "# "
HEADING_PREFIXES = ("## ", "### ")
MAPPING_HEADING_PREFIX = "### Mapping:"
BULLET_PREFIX = "- "
TABLE_CELL_FENCE = "|"
TABLE_HEADER_ROWS = 2


class Level(IntEnum):
    ONE = 1
    TWO = 2
    THREE = 3


def level_label(level: Level) -> str:
    """Name the case a level stands for, as the levels table names it."""
    return f"level-{level.value}"


def _body_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if lines and lines[0].strip() == FRONT_MATTER_FENCE:
        for index in range(1, len(lines)):
            if lines[index].strip() == FRONT_MATTER_FENCE:
                return lines[index + 1 :]
    return lines


def _is_heading(line: str) -> bool:
    return line.startswith(HEADING_PREFIXES)


def _trim_blank_edges(lines: list[str]) -> list[str]:
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def _split_title_and_rest(lines: list[str]) -> tuple[str, list[str]]:
    for index, line in enumerate(lines):
        if line.startswith(TITLE_PREFIX):
            return line, lines[index + 1 :]
    raise ValueError(
        "document has no title line; start the document with a first-level "
        "heading of the form '# <title>', before its opening"
    )


def _split_opening(rest: list[str]) -> tuple[list[str], list[str]]:
    for index, line in enumerate(rest):
        if _is_heading(line):
            return _trim_blank_edges(rest[:index]), rest[index:]
    return _trim_blank_edges(rest), []


def _first_cell(row: str) -> str:
    return row.strip().strip(TABLE_CELL_FENCE).split(TABLE_CELL_FENCE)[0].strip()


def _is_table_row(line: str) -> bool:
    return line.strip().startswith(TABLE_CELL_FENCE)


def _level_two_body(sections: list[str]) -> list[str]:
    emitted: list[str] = []
    in_mapping = False
    table_rows_seen = 0
    rule_lines: list[str] = []

    def flush_rule() -> None:
        if rule_lines:
            emitted.append(BULLET_PREFIX + " ".join(rule_lines))
            rule_lines.clear()

    for line in sections:
        stripped = line.strip()
        if _is_heading(line):
            flush_rule()
            if emitted:
                emitted.append("")
            emitted.append(line)
            in_mapping = line.startswith(MAPPING_HEADING_PREFIX)
            table_rows_seen = 0
        elif not stripped:
            flush_rule()
        elif in_mapping and _is_table_row(line):
            table_rows_seen += 1
            if table_rows_seen > TABLE_HEADER_ROWS:
                emitted.append(BULLET_PREFIX + _first_cell(line))
        elif in_mapping:
            emitted.append(stripped)
        elif stripped.startswith(BULLET_PREFIX):
            flush_rule()
            rule_lines.append(stripped[len(BULLET_PREFIX) :])
        elif rule_lines and not _is_table_row(line):
            rule_lines.append(stripped)
    flush_rule()
    return emitted


def derive_view(text: str, path: str, level: Level) -> str:
    """Return the view of one document at one level, newline terminated."""
    if level is Level.THREE:
        return text if text.endswith("\n") else text + "\n"
    title, rest = _split_title_and_rest(_body_lines(text))
    opening, sections = _split_opening(rest)
    view = [path, title, "", *opening]
    if level is Level.TWO and sections:
        view.extend(["", *_level_two_body(sections)])
    return "\n".join(view) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--level",
        type=int,
        required=True,
        choices=[level.value for level in Level],
    )
    parser.add_argument("file", type=Path)
    arguments = parser.parse_args(argv)
    try:
        text = arguments.file.read_text(encoding="utf-8")
        sys.stdout.write(
            derive_view(text, arguments.file.as_posix(), Level(arguments.level))
        )
    except (OSError, ValueError) as error:
        sys.stderr.write(f"{arguments.file}: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Derive the level views of a document written in the template form.

The form is the PDR or ADR template or an output-kind or variant spec template.
A proof of concept for the form: the views follow from a document's structure
alone, so a parser in the SPX CLI can derive the same views. A document in that
form holds a title, an opening, subsection headings, rules opened by a slug, and
tables. A Mapping and an Evaluate each form their own subsection of one sentence
and a case table. A Scenario rule holds only its slug on its first line, and its
Given, When, Then, and And steps follow as indented bullets.
Level 1 is the path, the title, and the opening. Level 2 adds each heading, each
rule's slug and sentence, and the first column of each Mapping and Evaluate
table, the case column; a Scenario rule contributes its slug, and its steps stay
at level 3. Level 3 is the whole file. A record whose only table is an Evaluate
case table takes the same level 2 view.

Usage: python3 -m outcomeeng.product_tree_levels --level 1|2|3 <file>
"""

from __future__ import annotations

import argparse
import sys
from enum import IntEnum
from pathlib import Path

FRONT_MATTER_FENCE = "---"
TITLE_PREFIX = "# "
HEADING_PREFIXES = ("## ", "### ")
MAPPING_HEADING_PREFIX = "### Test.Mapping:"
EVALUATE_HEADING_PREFIX = "### Evaluate:"
CODE_FENCE_PREFIXES = ("```", "~~~")
BULLET_PREFIX = "- "
TABLE_CELL_FENCE = "|"
TABLE_HEADER_ROWS = 2


class MissingTitleError(ValueError):
    """Raised when a document holds no title line."""


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


def _is_fence(line: str) -> bool:
    return line.lstrip().startswith(CODE_FENCE_PREFIXES)


def _fenced_flags(lines: list[str]) -> list[bool]:
    """Flag each line that is a code fence or lies between two of them."""
    flags: list[bool] = []
    inside = False
    for line in lines:
        fence = _is_fence(line)
        flags.append(inside or fence)
        if fence:
            inside = not inside
    return flags


def _trim_blank_edges(lines: list[str]) -> list[str]:
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def _split_title_and_rest(lines: list[str]) -> tuple[str, list[str]]:
    fenced = _fenced_flags(lines)
    for position, line in enumerate(lines):
        if line.startswith(TITLE_PREFIX) and not fenced[position]:
            return line, lines[position + 1 :]
    raise MissingTitleError("The document holds no title line")


def _split_opening(rest: list[str]) -> tuple[list[str], list[str]]:
    fenced = _fenced_flags(rest)
    for index, line in enumerate(rest):
        if _is_heading(line) and not fenced[index]:
            return _trim_blank_edges(rest[:index]), rest[index:]
    return _trim_blank_edges(rest), []


def _first_cell(row: str) -> str:
    return row.strip().strip(TABLE_CELL_FENCE).split(TABLE_CELL_FENCE)[0].strip()


def _is_table_row(line: str) -> bool:
    return line.strip().startswith(TABLE_CELL_FENCE)


class _LevelTwoView:
    """Collect the level 2 lines of the sections that follow a document's opening."""

    def __init__(self) -> None:
        self.emitted: list[str] = []
        self._rule_lines: list[str] = []
        self._sentence_lines: list[str] = []
        self._lists_cases = False
        self._in_sentence_subsection = False
        self._table_rows_seen = 0

    def flush_sentence(self) -> None:
        if self._sentence_lines:
            self.emitted.append(" ".join(self._sentence_lines))
            self._sentence_lines.clear()

    def flush_rule(self) -> None:
        self.flush_sentence()
        if self._rule_lines:
            self.emitted.append(BULLET_PREFIX + " ".join(self._rule_lines))
            self._rule_lines.clear()

    def consume(self, line: str) -> None:
        stripped = line.strip()
        if _is_heading(line):
            self._open_subsection(line)
        elif not stripped:
            self.flush_rule()
        elif self._in_sentence_subsection:
            self._consume_sentence_subsection(line, stripped)
        else:
            self._consume_rule(line, stripped)

    def _open_subsection(self, heading: str) -> None:
        self.flush_rule()
        if self.emitted:
            self.emitted.append("")
        self.emitted.append(heading)
        self._lists_cases = heading.startswith(
            (MAPPING_HEADING_PREFIX, EVALUATE_HEADING_PREFIX)
        )
        self._in_sentence_subsection = self._lists_cases
        self._table_rows_seen = 0

    def _consume_sentence_subsection(self, line: str, stripped: str) -> None:
        if not _is_table_row(line):
            self._sentence_lines.append(stripped)
            return
        self.flush_sentence()
        self._table_rows_seen += 1
        if self._table_rows_seen > TABLE_HEADER_ROWS:
            self.emitted.append(BULLET_PREFIX + _first_cell(line))

    def _consume_rule(self, line: str, stripped: str) -> None:
        if line.startswith(BULLET_PREFIX):
            self.flush_rule()
            self._rule_lines.append(line[len(BULLET_PREFIX) :].strip())
        elif (
            self._rule_lines
            and not _is_table_row(line)
            and not stripped.startswith(BULLET_PREFIX)
        ):
            self._rule_lines.append(stripped)


def _level_two_body(sections: list[str]) -> list[str]:
    view = _LevelTwoView()
    for line, in_fence in zip(sections, _fenced_flags(sections), strict=True):
        if not in_fence:
            view.consume(line)
    view.flush_rule()
    return view.emitted


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
    text = arguments.file.read_text(encoding="utf-8")
    sys.stdout.write(
        derive_view(text, arguments.file.as_posix(), Level(arguments.level))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

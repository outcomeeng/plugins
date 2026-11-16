"""Generated Codex configurations and Claude Code definitions for native auditor-dispatch refusal evidence.

Every name a case introduces is fresh per call, so a case selects only the
shape the governing rule names: a configuration that parses, one that does
not, one that already holds the writable-roots table, and a definition whose
`tools` grant is absent or empty. Every table, key, and field name the product
owns is imported from its owning module.
"""

from __future__ import annotations

import json
from enum import Enum
from uuid import uuid4

from outcomeeng.distribution.agents import AGENT_TOOLS_FIELD
from outcomeeng.distribution.contracts import FRONTMATTER_DELIMITER
from outcomeeng.distribution.native_auditor_dispatch import (
    CODEX_SANDBOX_WORKSPACE_WRITE_TABLE,
    CODEX_WRITABLE_ROOTS_KEY,
)


def _name() -> str:
    """A fresh bare TOML key: a letter, then hexadecimal digits."""
    return f"k{uuid4().hex}"


def _text() -> str:
    """A fresh TOML basic string; JSON string syntax is a subset of it."""
    return json.dumps(uuid4().hex)


def _held_entries() -> str:
    """Top-level keys of four value types, then a table and an array of tables."""
    return (
        f"{_name()} = {_text()}\n"
        f"{_name()} = {uuid4().int % 1000}\n"
        f"{_name()} = true\n"
        f"{_name()} = [{_text()}, {_text()}]\n"
        f"\n[{_name()}]\n{_name()} = {_text()}\n"
        f"\n[[{_name()}]]\n{_name()} = {_text()}\n"
    )


def generated_preserved_codex_configs() -> tuple[str, ...]:
    """Parseable configurations without the writable-roots table, ending with and without a newline."""
    top_level_only = f"{_name()} = {_text()}\n{_name()} = false\n"
    return (
        _held_entries(),
        _held_entries().rstrip("\n"),
        top_level_only,
        top_level_only.rstrip("\n"),
    )


def generated_unparseable_codex_configs() -> tuple[str, ...]:
    """Configurations TOML rejects: an unterminated table header, a key without a value, and a repeated key."""
    repeated = _name()
    return (
        f"{_held_entries()}[{_name()}\n",
        f"{_name()} =\n",
        f"{repeated} = {_text()}\n{repeated} = {_text()}\n",
    )


def generated_sandbox_table_configs() -> tuple[str, ...]:
    """Parseable configurations that already hold the writable-roots table, in each TOML form that declares it."""
    roots = f"[{_text()}]"
    return (
        f"[{CODEX_SANDBOX_WORKSPACE_WRITE_TABLE}]\n",
        f"{_held_entries()}\n[{CODEX_SANDBOX_WORKSPACE_WRITE_TABLE}]\n"
        f"{CODEX_WRITABLE_ROOTS_KEY} = {roots}\n",
        f"{CODEX_SANDBOX_WORKSPACE_WRITE_TABLE}.{CODEX_WRITABLE_ROOTS_KEY} = {roots}\n",
        f"{CODEX_SANDBOX_WORKSPACE_WRITE_TABLE} = {{ {CODEX_WRITABLE_ROOTS_KEY} = {roots} }}\n",
    )


class GrantAbsence(Enum):
    """How a Claude Code definition declares no `tools` grant."""

    FIELD_REMOVED = "field-removed"
    EMPTY_STRING = "empty-string"
    EMPTY_LIST = "empty-list"


def definition_without_grants(text: str, absence: GrantAbsence) -> str:
    """A Markdown agent definition with its `tools` field removed or emptied, every other line unchanged.

    The field's line and any indented continuation lines of it inside the
    frontmatter are replaced; a definition that carries no field gains an
    empty one at the frontmatter's end for the two empty forms.
    """
    lines = text.splitlines(keepends=True)
    opener = f"{FRONTMATTER_DELIMITER}\n"
    if not lines or lines[0] != opener:
        raise ValueError("expected YAML frontmatter opener")
    closing = next(
        index
        for index, line in enumerate(lines[1:], start=1)
        if line.rstrip("\n") == FRONTMATTER_DELIMITER
    )
    replacement = {
        GrantAbsence.FIELD_REMOVED: (),
        GrantAbsence.EMPTY_STRING: (f'{AGENT_TOOLS_FIELD}: ""\n',),
        GrantAbsence.EMPTY_LIST: (f"{AGENT_TOOLS_FIELD}: []\n",),
    }[absence]
    frontmatter: list[str] = []
    inside_field = False
    placed = False
    for line in lines[1:closing]:
        if line.startswith(f"{AGENT_TOOLS_FIELD}:"):
            inside_field = True
            frontmatter.extend(replacement)
            placed = True
            continue
        if inside_field and line[:1] in {" ", "\t"}:
            continue
        inside_field = False
        frontmatter.append(line)
    if not placed:
        frontmatter.extend(replacement)
    return "".join((lines[0], *frontmatter, *lines[closing:]))

"""Conformance harness for eval definition loading.

The eval definition schema is the oracle. This harness reads it by path, writes
real eval directories, and reports what the real loader did with them. Every
verdict lives in the linked tests.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from outcomeeng_evals.definition import (
    EVAL_TOML_FILENAME,
    EvalDefinition,
    load_definition,
)
from outcomeeng_testing.harnesses.evals import toml_basic_string

EVAL_DEFINITION_SCHEMA_PATH = (
    Path(__file__).parents[2]
    / "spx/13-infrastructure.enabler/25-eval-harness.enabler"
    / "contracts/eval-definition.schema.json"
)

CASES_FILENAME = "cases.jsonl"
PROMPT_FILENAME = "prompt.md"
TITLE_VALUE = "definition-probe"


@dataclass(frozen=True)
class DefinitionLoad:
    """What the real loader did with one eval directory."""

    toml_path: Path
    definition: EvalDefinition | None
    error: Exception | None


def eval_definition_schema() -> dict[str, object]:
    """Read the eval definition schema the spec links as its contract."""

    with EVAL_DEFINITION_SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        return cast(dict[str, object], json.load(schema_file))


def schema_properties() -> dict[str, dict[str, object]]:
    """Return the schema's declared properties by field name."""

    return cast(dict[str, dict[str, object]], eval_definition_schema()["properties"])


def schema_required_fields() -> tuple[str, ...]:
    """Return the fields the schema requires."""

    return tuple(cast(list[str], eval_definition_schema()["required"]))


def schema_path_fields() -> tuple[str, ...]:
    """Return the required fields the loader resolves to files beside the TOML."""

    return tuple(
        field for field in schema_required_fields() if field in _PATH_FIELD_FILENAMES
    )


_PATH_FIELD_FILENAMES = {"cases": CASES_FILENAME, "prompt": PROMPT_FILENAME}


def _toml_value(value: object) -> str:
    if isinstance(value, str):
        return toml_basic_string(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    return json.dumps(value)


def valid_required_fields() -> dict[str, object]:
    """Return a complete required-field set pointing at the files written beside it."""

    return {
        field: _PATH_FIELD_FILENAMES.get(field, TITLE_VALUE)
        for field in schema_required_fields()
    }


def load_written_definition(
    directory: Path,
    fields: Mapping[str, object],
    *,
    omit_files_for: tuple[str, ...] = (),
) -> DefinitionLoad:
    """Write an eval directory declaring ``fields`` and load it with the real loader.

    ``omit_files_for`` names path fields whose target file is not written.
    """

    directory.mkdir(parents=True, exist_ok=True)
    toml_path = directory / EVAL_TOML_FILENAME
    toml_path.write_text(
        "".join(f"{key} = {_toml_value(value)}\n" for key, value in fields.items()),
        encoding="utf-8",
    )
    for field, filename in _PATH_FIELD_FILENAMES.items():
        if field not in omit_files_for:
            (directory / filename).write_text("", encoding="utf-8")
    try:
        return DefinitionLoad(toml_path, load_definition(toml_path), None)
    except (FileNotFoundError, KeyError, ValueError) as error:
        return DefinitionLoad(toml_path, None, error)


ARBITRARY_MODEL = "claude-sonnet-4-5"
NON_STRING_MODEL = 1
CI_PLUGIN_DIR = "dist/claude/product-tree"
CI_OWNED_PATH_EXACT = "AGENTS.md"
CI_OWNED_PATH_DIRECTORY = "src/plugins/product-tree/skills/merge"
CI_SMOKE_CASE = "happy-path"

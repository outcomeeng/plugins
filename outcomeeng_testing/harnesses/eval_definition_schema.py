"""Judge eval.toml tables by the eval-definition schema and by the loader.

The eval-harness Node declares the table an ``eval.toml`` parses to in
``contracts/eval-definition.schema.json``. Its conformance evidence takes the
schema's verdict from an independent JSON Schema validator and the loader's
verdict from ``outcomeeng_evals.definition.load_definition`` on the same
table, so a loader that drifts from the contract fails the evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from jsonschema import Draft202012Validator

from outcomeeng_evals.definition import load_definition

EVAL_DEFINITION_SCHEMA_PATH: Final = (
    Path(__file__).resolve().parents[2]
    / "spx"
    / "13-infrastructure.enabler"
    / "25-eval-harness.enabler"
    / "contracts"
    / "eval-definition.schema.json"
)
EVAL_TOML_FILENAME: Final = "eval.toml"

type TomlScalar = str | int | float
type TomlValue = TomlScalar | list[str]
type EvalTable = dict[str, TomlValue]


@dataclass(frozen=True)
class DefinitionShape:
    """One eval.toml table and the verdict the contract gives it."""

    case_id: str
    table: EvalTable
    accepted: bool


def required_table(**fields: TomlValue) -> EvalTable:
    """Return the three required fields, overridden or extended by ``fields``."""

    table: EvalTable = {"title": "eval", "cases": "cases.jsonl", "prompt": "prompt.md"}
    table.update(fields)
    return table


def table_without(field: str) -> EvalTable:
    """Return the required table with ``field`` left out."""

    table = required_table()
    del table[field]
    return table


def eval_definition_validator() -> Draft202012Validator:
    """Return a validator over the schema the Node's contract file declares."""

    schema = json.loads(EVAL_DEFINITION_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def schema_accepts(table: EvalTable) -> bool:
    """Return whether the contract's schema accepts ``table``."""

    return eval_definition_validator().is_valid(table)


def loader_accepts(table: EvalTable) -> bool:
    """Return whether the loader accepts ``table`` written as an eval.toml.

    The cases and prompt files the table names exist beside the TOML file, so
    the verdict judges the table's fields and not the presence of those files.
    """

    with TemporaryDirectory() as tmp:
        directory = Path(tmp)
        toml_path = directory / EVAL_TOML_FILENAME
        toml_path.write_text(render_toml(table), encoding="utf-8")
        for key in ("cases", "prompt"):
            value = table.get(key)
            if isinstance(value, str) and value and "/" not in value:
                (directory / value).write_text("", encoding="utf-8")
        try:
            load_definition(toml_path)
        except (KeyError, ValueError):
            return False
    return True


def render_toml(table: EvalTable) -> str:
    """Render a flat table of strings, numbers and string lists as TOML."""

    return "".join(f"{key} = {_render_value(value)}\n" for key, value in table.items())


def _render_value(value: TomlValue) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(item) for item in value) + "]"
    if isinstance(value, str):
        return json.dumps(value)
    return repr(value)

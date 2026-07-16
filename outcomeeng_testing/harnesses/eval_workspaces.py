"""Shared workspace harnesses for eval evidence tests."""

from __future__ import annotations

import json
import re
import shutil
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypeAlias

from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.producer_prompt import UTF8_ENCODING


EVAL_FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "evals"
PRODUCER_PROMPT_FIXTURE_ROOT = EVAL_FIXTURES_ROOT / "producer_prompt"
TomlScalar: TypeAlias = str | int | bool
TomlValue: TypeAlias = TomlScalar | list[TomlScalar]


@dataclass(frozen=True)
class EvalWorkspace:
    """One copied inert eval workspace."""

    fixture_root: Path
    repo_root: Path
    eval_toml: Path


def copy_eval_workspace(
    destination: Path,
    *,
    fixture_root: Path,
    workspace_root: Path,
) -> EvalWorkspace:
    """Copy one complete inert fixture repository into a temporary directory."""

    destination.mkdir(parents=True, exist_ok=True)
    repo_root = destination / workspace_root.name
    shutil.copytree(workspace_root, repo_root)
    eval_definitions = tuple(repo_root.rglob(EVAL_TOML_FILENAME))
    if len(eval_definitions) != 1:
        raise ValueError(
            f"{workspace_root}: expected one eval.toml, found {len(eval_definitions)}"
        )
    return EvalWorkspace(
        fixture_root=fixture_root,
        repo_root=repo_root,
        eval_toml=eval_definitions[0],
    )


def replace_workspace_file(
    workspace: EvalWorkspace,
    *,
    relative_path: Path,
    fixture_path: Path,
) -> Path:
    """Replace a copied workspace file with one inert fixture variant."""

    destination = workspace.repo_root / relative_path
    shutil.copyfile(fixture_path, destination)
    return destination


def replace_text_once(path: Path, *, old: str, new: str) -> None:
    """Replace one expected text occurrence in a copied workspace file."""

    text = path.read_text(encoding=UTF8_ENCODING)
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{path}: expected one occurrence, found {count}")
    path.write_text(text.replace(old, new, 1), encoding=UTF8_ENCODING)


def set_toml_field(
    path: Path,
    *,
    table: str | None,
    field: str,
    value: TomlValue,
) -> None:
    """Set one TOML field while preserving the copied fixture around it."""

    _mutate_toml_field(path, table=table, field=field, value=value)


def remove_toml_field(path: Path, *, table: str | None, field: str) -> None:
    """Remove one TOML field while preserving the copied fixture around it."""

    _mutate_toml_field(path, table=table, field=field, value=None)


def _mutate_toml_field(
    path: Path,
    *,
    table: str | None,
    field: str,
    value: TomlValue | None,
) -> None:
    original = path.read_text(encoding=UTF8_ENCODING)
    tomllib.loads(original)
    lines = original.splitlines()
    start, end = _toml_table_bounds(lines, table=table)
    field_pattern = re.compile(rf"^\s*{re.escape(field)}\s*=")
    matching = [
        index for index in range(start, end) if field_pattern.match(lines[index])
    ]
    if len(matching) > 1:
        raise ValueError(f"{path}: field {field!r} occurs more than once")
    value_end = (
        _toml_field_value_end(
            lines,
            start=matching[0],
            table_end=end,
            table=table,
            field=field,
        )
        if matching
        else None
    )
    if value is None:
        if value_end is None:
            raise ValueError(f"{path}: field {field!r} is absent")
        del lines[matching[0] : value_end]
    elif value_end is not None:
        lines[matching[0] : value_end] = [f"{field} = {_toml_value(value)}"]
    else:
        lines.insert(end, f"{field} = {_toml_value(value)}")
    updated = "\n".join(lines) + "\n"
    tomllib.loads(updated)
    path.write_text(updated, encoding=UTF8_ENCODING)


def _toml_field_value_end(
    lines: list[str],
    *,
    start: int,
    table_end: int,
    table: str | None,
    field: str,
) -> int:
    """Return the exclusive line end of one parser-complete TOML value."""

    header = [] if table is None else [f"[{table}]"]
    for candidate_end in range(start + 1, table_end + 1):
        candidate = "\n".join([*header, *lines[start:candidate_end]]) + "\n"
        try:
            parsed = tomllib.loads(candidate)
        except tomllib.TOMLDecodeError:
            continue
        owner = parsed if table is None else parsed.get(table)
        if isinstance(owner, dict) and field in owner:
            return candidate_end
    raise ValueError(f"field {field!r} has no complete TOML value")


def _toml_table_bounds(lines: list[str], *, table: str | None) -> tuple[int, int]:
    headers = [
        (index, match.group("name"))
        for index, line in enumerate(lines)
        if (match := re.fullmatch(r"\s*\[(?P<name>[^]]+)]\s*", line)) is not None
    ]
    if table is None:
        return 0, headers[0][0] if headers else len(lines)
    matching = [item for item in headers if item[1] == table]
    if len(matching) != 1:
        raise ValueError(f"expected exactly one TOML table {table!r}")
    header_index = matching[0][0]
    later_headers = [index for index, _name in headers if index > header_index]
    return header_index + 1, later_headers[0] if later_headers else len(lines)


def _toml_value(value: TomlValue) -> str:
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    return "[" + ", ".join(_toml_value(item) for item in value) + "]"


def with_temp_workspace(assertion: Callable[[Path], None]) -> Callable[[], None]:
    """Run a no-argument assertion inside a temporary workspace."""

    def run_assertion() -> None:
        with TemporaryDirectory() as temp_dir:
            assertion(Path(temp_dir))

    return run_assertion

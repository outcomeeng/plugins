"""Evidence harness for eval case loading, grading, and suite execution.

Exposes the captured eval fixtures, a case-prompt builder, and JSONL writing as
observations and handles; every verdict lives in the linked tests.
"""

from __future__ import annotations

import json
from pathlib import Path

from outcomeeng_evals.case import Case
from outcomeeng_evals.cli.commands.run import _render_prompt

_FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures/evals"


def fixture_path(name: str) -> Path:
    """Return the path of one inert eval fixture."""

    return _FIXTURE_ROOT / name


def fixture_text(name: str) -> str:
    """Read one inert eval fixture as text."""

    return fixture_path(name).read_text(encoding="utf-8")


def fixture_json(name: str) -> object:
    """Read one inert eval fixture as JSON."""

    with fixture_path(name).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def response_sequences() -> dict[str, tuple[str, ...]]:
    """Return the captured per-trial response sequences keyed by sequence name."""

    paths = fixture_json("suite_response_sequences.json")
    if not isinstance(paths, dict):
        raise TypeError("suite_response_sequences.json holds no object")
    return {
        name: tuple(fixture_text(filename) for filename in filenames)
        for name, filenames in paths.items()
    }


def fixture_prompt(case: Case) -> str:
    """Render a case's input as the prompt the stub runners receive."""

    return json.dumps(case.input)


def render_prompt(template: str, case: Case) -> str:
    """Render a prompt template through the run command's renderer."""

    return _render_prompt(template, case)


def write_jsonl_record(path: Path, record: dict[str, object]) -> None:
    """Write one record as a single-line JSONL case file."""

    with path.open("w", encoding="utf-8") as output:
        json.dump(record, output)
        output.write("\n")

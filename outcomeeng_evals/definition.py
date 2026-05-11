"""EvalDefinition TOML loader.

Each per-eval directory carries an ``eval.toml`` declaring the title,
relative paths to ``cases.jsonl`` and ``prompt.md``, and (optionally) a
suite threshold and trial count. Paths in the TOML are resolved relative
to the TOML file's directory.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SUITE_THRESHOLD = 0.85
DEFAULT_TRIALS_PER_CASE = 1

_REQUIRED_TITLE = "title"
_REQUIRED_CASES = "cases"
_REQUIRED_PROMPT = "prompt"
_OPTIONAL_THRESHOLD = "threshold"
_OPTIONAL_TRIALS = "trials"


@dataclass(frozen=True)
class EvalDefinition:
    """An eval's durable contract: title, case file, prompt file, gate settings."""

    title: str
    cases_path: Path
    prompt_template_path: Path
    threshold: float
    trials: int


def load_definition(toml_path: Path) -> EvalDefinition:
    """Parse an ``eval.toml`` file and return the resolved definition.

    Paths in the TOML are interpreted relative to the TOML file's
    directory. Required fields raise ``KeyError``; type errors and missing
    target files raise ``ValueError``.
    """
    raw = _load_toml(toml_path)
    title = _required_str(raw, _REQUIRED_TITLE)
    cases_rel = _required_str(raw, _REQUIRED_CASES)
    prompt_rel = _required_str(raw, _REQUIRED_PROMPT)

    eval_dir = toml_path.parent
    cases_path = (eval_dir / cases_rel).resolve()
    prompt_path = (eval_dir / prompt_rel).resolve()

    if not cases_path.is_file():
        msg = f"{toml_path}: cases file not found: {cases_path}"
        raise FileNotFoundError(msg)
    if not prompt_path.is_file():
        msg = f"{toml_path}: prompt file not found: {prompt_path}"
        raise FileNotFoundError(msg)

    threshold = _optional_float(raw, _OPTIONAL_THRESHOLD, DEFAULT_SUITE_THRESHOLD)
    trials = _optional_int(raw, _OPTIONAL_TRIALS, DEFAULT_TRIALS_PER_CASE)

    return EvalDefinition(
        title=title,
        cases_path=cases_path,
        prompt_template_path=prompt_path,
        threshold=threshold,
        trials=trials,
    )


def _load_toml(toml_path: Path) -> dict[str, Any]:
    if not toml_path.is_file():
        msg = f"eval definition not found: {toml_path}"
        raise FileNotFoundError(msg)
    with toml_path.open("rb") as fh:
        return tomllib.load(fh)


def _required_str(data: dict[str, Any], key: str) -> str:
    if key not in data:
        msg = f"missing required field {key!r}"
        raise KeyError(key, msg)
    value = data[key]
    if not isinstance(value, str) or not value:
        msg = f"field {key!r} must be a non-empty string, got {type(value).__name__}"
        raise ValueError(msg)
    return value


def _optional_float(data: dict[str, Any], key: str, default: float) -> float:
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        msg = f"field {key!r} must be a number, got {type(value).__name__}"
        raise ValueError(msg)
    return float(value)


def _optional_int(data: dict[str, Any], key: str, default: int) -> int:
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"field {key!r} must be an integer, got {type(value).__name__}"
        raise ValueError(msg)
    if value < 1:
        msg = f"field {key!r} must be >= 1, got {value}"
        raise ValueError(msg)
    return int(value)

"""EvalDefinition TOML loader.

Each per-eval directory carries an ``eval.toml`` declaring the title,
relative paths to ``cases.jsonl`` and ``prompt.md``, and (optionally) a
suite threshold and trial count. Paths in the TOML are resolved relative
to the TOML file's directory.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


DEFAULT_SUITE_THRESHOLD = 0.85
DEFAULT_TRIALS_PER_CASE = 1
DEFAULT_CI_POLICY = "full"
DEFAULT_MODEL = "sonnet"
# Upper bound on ``trials`` from an ``eval.toml``: a misconfigured value
# like ``trials = 10000`` would otherwise fire that many subprocesses.
# Mirrors the ``--workers`` CLI cap (16); 100 leaves ample headroom for
# pass@k stability work without being a runaway risk.
MAX_TRIALS_PER_CASE = 100

EVAL_TOML_FILENAME = "eval.toml"
RUNS_DIRNAME = "runs"

# The only glob an owned path may carry, and the characters its remainder may
# use. The alphabet is an allowlist rather than a list of forbidden globs: a
# denylist admits every metacharacter nobody thought to forbid, and this
# contract has to hold against a CI provider's glob engine the harness cannot
# introspect.
OWNED_PATH_RECURSIVE_SUFFIX = "/**"
OWNED_PATH_ALPHABET = re.compile(r"[A-Za-z0-9._/-]+")

_REQUIRED_TITLE = "title"
_REQUIRED_CASES = "cases"
_REQUIRED_PROMPT = "prompt"
_OPTIONAL_THRESHOLD = "threshold"
_OPTIONAL_TRIALS = "trials"
_OPTIONAL_PLUGIN_DIR = "plugin_dir"
_OPTIONAL_MODEL = "model"
_OPTIONAL_OWNED_PATHS = "owned_paths"
_OPTIONAL_SMOKE_CASES = "smoke_cases"
_OPTIONAL_CI_POLICY = "ci_policy"
_INHERIT_MODEL = "inherit"


class CiPolicy(StrEnum):
    """How automated CI treats an eval suite."""

    FULL = "full"
    MANUAL = "manual"


@dataclass(frozen=True)
class EvalDefinition:
    """An eval's durable contract: title, case file, prompt file, gate settings."""

    title: str
    cases_path: Path
    prompt_template_path: Path
    threshold: float
    trials: int
    plugin_dir: Path | None
    model: str
    owned_paths: tuple[str, ...]
    smoke_case_ids: tuple[str, ...]
    ci_policy: CiPolicy


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

    threshold = _optional_float(
        raw,
        _OPTIONAL_THRESHOLD,
        DEFAULT_SUITE_THRESHOLD,
        min_value=0.0,
        max_value=1.0,
    )
    trials = _optional_int(
        raw,
        _OPTIONAL_TRIALS,
        DEFAULT_TRIALS_PER_CASE,
        min_value=1,
        max_value=MAX_TRIALS_PER_CASE,
    )
    plugin_dir = _optional_path(raw, _OPTIONAL_PLUGIN_DIR)
    model = _optional_model(raw, _OPTIONAL_MODEL)
    owned_paths = _optional_owned_paths(raw, _OPTIONAL_OWNED_PATHS)
    smoke_case_ids = _optional_str_tuple(raw, _OPTIONAL_SMOKE_CASES)
    ci_policy = _optional_ci_policy(raw, _OPTIONAL_CI_POLICY)

    return EvalDefinition(
        title=title,
        cases_path=cases_path,
        prompt_template_path=prompt_path,
        threshold=threshold,
        trials=trials,
        plugin_dir=plugin_dir,
        model=model,
        owned_paths=owned_paths,
        smoke_case_ids=smoke_case_ids,
        ci_policy=ci_policy,
    )


def _load_toml(toml_path: Path) -> dict[str, Any]:
    if not toml_path.is_file():
        msg = f"eval definition not found: {toml_path}"
        raise FileNotFoundError(msg)
    with toml_path.open("rb") as fh:
        return tomllib.load(fh)


def _required_str(data: dict[str, Any], key: str) -> str:
    if key not in data:
        # Single-arg KeyError matching Python's dict contract; the
        # diagnostic context is the key name itself. The two-arg form
        # (KeyError(key, msg)) produces a confusing tuple-repr.
        raise KeyError(key)
    value = data[key]
    if not isinstance(value, str) or not value:
        msg = f"field {key!r} must be a non-empty string, got {type(value).__name__}"
        raise ValueError(msg)
    return value


def _optional_float(
    data: dict[str, Any],
    key: str,
    default: float,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        msg = f"field {key!r} must be a number, got {type(value).__name__}"
        raise ValueError(msg)
    result = float(value)
    if min_value is not None and result < min_value:
        msg = f"field {key!r} must be >= {min_value}, got {result}"
        raise ValueError(msg)
    if max_value is not None and result > max_value:
        msg = f"field {key!r} must be <= {max_value}, got {result}"
        raise ValueError(msg)
    return result


def _optional_int(
    data: dict[str, Any],
    key: str,
    default: int,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"field {key!r} must be an integer, got {type(value).__name__}"
        raise ValueError(msg)
    if min_value is not None and value < min_value:
        msg = f"field {key!r} must be >= {min_value}, got {value}"
        raise ValueError(msg)
    if max_value is not None and value > max_value:
        msg = f"field {key!r} must be <= {max_value}, got {value}"
        raise ValueError(msg)
    return int(value)


def _optional_path(data: dict[str, Any], key: str) -> Path | None:
    if key not in data:
        return None
    value = data[key]
    if not isinstance(value, str) or not value:
        msg = f"field {key!r} must be a non-empty string, got {type(value).__name__}"
        raise ValueError(msg)
    return Path(value)


def _optional_model(data: dict[str, Any], key: str) -> str:
    if key not in data:
        return DEFAULT_MODEL
    return validate_model(data[key], key)


def validate_model(value: Any, key: str) -> str:
    """Validate a model name from a durable or CLI-owned configuration field."""
    if not isinstance(value, str) or not value:
        msg = f"field {key!r} must be a non-empty string, got {type(value).__name__}"
        raise ValueError(msg)
    if value == _INHERIT_MODEL:
        msg = f"field {key!r} must not be {_INHERIT_MODEL!r}"
        raise ValueError(msg)
    return value


def _optional_str_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    if key not in data:
        return ()
    value = data[key]
    if not isinstance(value, list):
        msg = f"field {key!r} must be a list of non-empty strings, got {type(value).__name__}"
        raise ValueError(msg)
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            msg = f"field {key!r} must contain only non-empty strings"
            raise ValueError(msg)
        result.append(item)
    return tuple(result)


def _optional_owned_paths(data: dict[str, Any], key: str) -> tuple[str, ...]:
    """Load ``owned_paths``, restricted to the shapes CI matching agrees on.

    An owned path is matched two ways: locally by ``fnmatch`` when the planner
    selects suites from changed paths, and remotely by the CI provider's glob
    engine when the generated trigger filter decides whether the job starts at
    all. The two engines agree on an exact literal and on a trailing ``/**``,
    and disagree elsewhere — ``fnmatch``'s ``*`` spans ``/`` while the CI
    provider's does not. Restricting the shape keeps the two in lockstep, so a
    path that selects a suite locally also starts the job remotely.
    """

    paths = _optional_str_tuple(data, key)
    for path in paths:
        body = path.removesuffix(OWNED_PATH_RECURSIVE_SUFFIX)
        if not OWNED_PATH_ALPHABET.fullmatch(body):
            allowed = f"an exact path or one ending in {OWNED_PATH_RECURSIVE_SUFFIX!r}"
            msg = (
                f"field {key!r} entry {path!r} must be {allowed} — a glob the "
                f"local planner and the CI trigger filter match differently "
                f"would select a suite the CI job never starts"
            )
            raise ValueError(msg)
    return paths


def _optional_ci_policy(data: dict[str, Any], key: str) -> CiPolicy:
    if key not in data:
        return CiPolicy(DEFAULT_CI_POLICY)
    value = data[key]
    if not isinstance(value, str):
        msg = f"field {key!r} must be a string, got {type(value).__name__}"
        raise ValueError(msg)
    try:
        return CiPolicy(value)
    except ValueError as exc:
        allowed = ", ".join(policy.value for policy in CiPolicy)
        msg = f"field {key!r} must be one of: {allowed}"
        raise ValueError(msg) from exc

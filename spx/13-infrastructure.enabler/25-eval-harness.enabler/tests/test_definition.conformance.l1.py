"""Conformance tests for EvalDefinition TOML loading.

The definition is the single declarative entry point for an eval; it
declares title, cases path, prompt template path, threshold, and trials.
Path values are relative to the TOML file's directory.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_evals.definition import (
    CiPolicy,
    DEFAULT_SUITE_THRESHOLD,
    DEFAULT_TRIALS_PER_CASE,
    MAX_TRIALS_PER_CASE,
    EvalDefinition,
    load_definition,
)


CASES_FILENAME = "cases.jsonl"
PROMPT_FILENAME = "prompt.md"
EVAL_FILENAME = "eval.toml"
TITLE = "shared-test-owned-constant-bag"
CUSTOM_THRESHOLD = 0.95
CUSTOM_TRIALS = 3
PLUGIN_DIR = "dist/claude/spec-tree"
OWNED_PATH = "src/plugins/spec-tree/skills/manage-pr/**"
SMOKE_CASE = "happy-path"


def _write_eval_dir(
    tmp_path: Path,
    *,
    toml_text: str,
    with_cases: bool = True,
    with_prompt: bool = True,
) -> Path:
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    (eval_dir / EVAL_FILENAME).write_text(toml_text, encoding="utf-8")
    if with_cases:
        (eval_dir / CASES_FILENAME).write_text("", encoding="utf-8")
    if with_prompt:
        (eval_dir / PROMPT_FILENAME).write_text("", encoding="utf-8")
    return eval_dir / EVAL_FILENAME


def test_loads_required_fields(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
        ),
    )

    definition = load_definition(toml_path)

    assert isinstance(definition, EvalDefinition)
    assert definition.title == TITLE


def test_resolves_cases_path_relative_to_toml_directory(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
        ),
    )

    definition = load_definition(toml_path)

    assert definition.cases_path == toml_path.parent / CASES_FILENAME


def test_resolves_prompt_path_relative_to_toml_directory(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
        ),
    )

    definition = load_definition(toml_path)

    assert definition.prompt_template_path == toml_path.parent / PROMPT_FILENAME


def test_applies_default_threshold_when_omitted(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
        ),
    )

    definition = load_definition(toml_path)

    assert definition.threshold == DEFAULT_SUITE_THRESHOLD


def test_applies_default_trials_when_omitted(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
        ),
    )

    definition = load_definition(toml_path)

    assert definition.trials == DEFAULT_TRIALS_PER_CASE


def test_uses_explicit_threshold_when_set(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
            f"threshold = {CUSTOM_THRESHOLD}\n"
        ),
    )

    definition = load_definition(toml_path)

    assert definition.threshold == pytest.approx(CUSTOM_THRESHOLD)


def test_uses_explicit_trials_when_set(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
            f"trials = {CUSTOM_TRIALS}\n"
        ),
    )

    definition = load_definition(toml_path)

    assert definition.trials == CUSTOM_TRIALS


def test_loads_optional_ci_metadata(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
            f'plugin_dir = "{PLUGIN_DIR}"\n'
            f'owned_paths = ["{OWNED_PATH}"]\n'
            f'smoke_cases = ["{SMOKE_CASE}"]\n'
            'ci_policy = "manual"\n'
        ),
    )

    definition = load_definition(toml_path)

    assert definition.plugin_dir == Path(PLUGIN_DIR)
    assert definition.owned_paths == (OWNED_PATH,)
    assert definition.smoke_case_ids == (SMOKE_CASE,)
    assert definition.ci_policy is CiPolicy.MANUAL


def test_accepts_trials_at_cap(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
            f"trials = {MAX_TRIALS_PER_CASE}\n"
        ),
    )

    definition = load_definition(toml_path)

    assert definition.trials == MAX_TRIALS_PER_CASE


def test_rejects_trials_above_cap(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
            f"trials = {MAX_TRIALS_PER_CASE + 1}\n"
        ),
    )

    with pytest.raises(ValueError, match="trials"):
        load_definition(toml_path)


def test_rejects_trials_below_one(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
            "trials = 0\n"
        ),
    )

    with pytest.raises(ValueError, match="trials"):
        load_definition(toml_path)


def test_rejects_missing_title(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(f'cases = "{CASES_FILENAME}"\nprompt = "{PROMPT_FILENAME}"\n'),
    )

    with pytest.raises((KeyError, ValueError), match="title"):
        load_definition(toml_path)


def test_rejects_missing_cases(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(f'title = "{TITLE}"\nprompt = "{PROMPT_FILENAME}"\n'),
    )

    with pytest.raises((KeyError, ValueError), match="cases"):
        load_definition(toml_path)


def test_rejects_missing_prompt(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(f'title = "{TITLE}"\ncases = "{CASES_FILENAME}"\n'),
    )

    with pytest.raises((KeyError, ValueError), match="prompt"):
        load_definition(toml_path)


def test_rejects_nonexistent_cases_file(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
        ),
        with_cases=False,
    )

    with pytest.raises((FileNotFoundError, ValueError), match="cases"):
        load_definition(toml_path)


def test_rejects_nonexistent_prompt_file(tmp_path: Path) -> None:
    toml_path = _write_eval_dir(
        tmp_path,
        toml_text=(
            f'title = "{TITLE}"\n'
            f'cases = "{CASES_FILENAME}"\n'
            f'prompt = "{PROMPT_FILENAME}"\n'
        ),
        with_prompt=False,
    )

    with pytest.raises((FileNotFoundError, ValueError), match="prompt"):
        load_definition(toml_path)

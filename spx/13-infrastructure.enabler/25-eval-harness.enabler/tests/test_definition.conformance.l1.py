"""Conformance tests for EvalDefinition TOML loading."""

from __future__ import annotations

import glob
import math
from pathlib import Path
from string import printable

import pytest

from outcomeeng.models import EVAL_PROFILE_MODELS, AgentProfile
from outcomeeng_evals.definition import (
    CASES_FIELD,
    DEFAULT_PROFILE,
    DEFAULT_SUITE_THRESHOLD,
    DEFAULT_TRIALS_PER_CASE,
    MAX_TRIALS_PER_CASE,
    MODEL_FIELD,
    OWNED_PATH_ALPHABET,
    OWNED_PATH_RECURSIVE_SUFFIX,
    OWNED_PATHS_FIELD,
    PROFILE_FIELD,
    PROMPT_FIELD,
    THRESHOLD_FIELD,
    TITLE_FIELD,
    TRIALS_FIELD,
    EvalDefinition,
    load_definition,
)
from outcomeeng_testing.evals.factories import (
    DEFAULT_DEFINITION_THRESHOLD,
    DEFAULT_DEFINITION_TRIALS,
    EVAL_CASES_FILENAME,
    EVAL_DEFINITION_TITLE,
    EVAL_PROMPT_FILENAME,
    make_ci_metadata_definition_case,
    write_eval_definition,
)


def test_loads_required_fields(tmp_path: Path) -> None:
    definition = load_definition(write_eval_definition(tmp_path))

    assert isinstance(definition, EvalDefinition)
    assert definition.title == EVAL_DEFINITION_TITLE


def test_resolves_cases_path_relative_to_toml_directory(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path)

    definition = load_definition(toml_path)

    assert definition.cases_path == (toml_path.parent / EVAL_CASES_FILENAME).resolve()


def test_resolves_prompt_path_relative_to_toml_directory(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path)

    definition = load_definition(toml_path)

    assert (
        definition.prompt_template_path
        == (toml_path.parent / EVAL_PROMPT_FILENAME).resolve()
    )


def test_applies_default_threshold_when_omitted(tmp_path: Path) -> None:
    definition = load_definition(write_eval_definition(tmp_path))

    assert definition.threshold == DEFAULT_SUITE_THRESHOLD


def test_applies_default_trials_when_omitted(tmp_path: Path) -> None:
    definition = load_definition(write_eval_definition(tmp_path))

    assert definition.trials == DEFAULT_TRIALS_PER_CASE


def test_applies_default_profile_when_omitted(tmp_path: Path) -> None:
    definition = load_definition(write_eval_definition(tmp_path))

    assert definition.profile is DEFAULT_PROFILE


def test_uses_explicit_threshold_when_set(tmp_path: Path) -> None:
    toml_path = write_eval_definition(
        tmp_path, fields={THRESHOLD_FIELD: DEFAULT_DEFINITION_THRESHOLD}
    )

    definition = load_definition(toml_path)

    assert math.isclose(definition.threshold, DEFAULT_DEFINITION_THRESHOLD)


def test_uses_explicit_trials_when_set(tmp_path: Path) -> None:
    toml_path = write_eval_definition(
        tmp_path, fields={TRIALS_FIELD: DEFAULT_DEFINITION_TRIALS}
    )

    definition = load_definition(toml_path)

    assert definition.trials == DEFAULT_DEFINITION_TRIALS


def test_loads_optional_ci_metadata(tmp_path: Path) -> None:
    case = make_ci_metadata_definition_case(tmp_path)

    definition = load_definition(case.eval_toml)

    assert definition.plugin_dir == case.plugin_dir
    assert definition.profile is case.profile
    assert definition.owned_paths == case.owned_paths
    assert definition.smoke_case_ids == case.smoke_case_ids
    assert definition.ci_policy is case.ci_policy


@pytest.mark.parametrize("profile", tuple(AgentProfile))
def test_uses_explicit_profile_when_set(tmp_path: Path, profile: AgentProfile) -> None:
    definition = load_definition(
        write_eval_definition(tmp_path, fields={PROFILE_FIELD: profile})
    )

    assert definition.profile is profile


def test_rejects_model(tmp_path: Path) -> None:
    toml_path = write_eval_definition(
        tmp_path,
        fields={MODEL_FIELD: EVAL_PROFILE_MODELS[DEFAULT_PROFILE].model},
    )

    with pytest.raises(ValueError, match=MODEL_FIELD):
        load_definition(toml_path)


@pytest.mark.parametrize("profile", tuple(AgentProfile))
def test_rejects_model_name_as_profile(tmp_path: Path, profile: AgentProfile) -> None:
    toml_path = write_eval_definition(
        tmp_path,
        fields={PROFILE_FIELD: EVAL_PROFILE_MODELS[profile].model},
    )

    with pytest.raises(ValueError, match=PROFILE_FIELD):
        load_definition(toml_path)


def test_rejects_non_string_profile(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path, fields={PROFILE_FIELD: 1})

    with pytest.raises(ValueError, match=PROFILE_FIELD):
        load_definition(toml_path)


def test_accepts_trials_at_cap(tmp_path: Path) -> None:
    toml_path = write_eval_definition(
        tmp_path, fields={TRIALS_FIELD: MAX_TRIALS_PER_CASE}
    )

    definition = load_definition(toml_path)

    assert definition.trials == MAX_TRIALS_PER_CASE


def test_rejects_trials_above_cap(tmp_path: Path) -> None:
    toml_path = write_eval_definition(
        tmp_path, fields={TRIALS_FIELD: MAX_TRIALS_PER_CASE + 1}
    )

    with pytest.raises((FileNotFoundError, KeyError, ValueError), match=TRIALS_FIELD):
        load_definition(toml_path)


def test_rejects_trials_below_one(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path, fields={TRIALS_FIELD: 0})

    with pytest.raises((FileNotFoundError, KeyError, ValueError), match=TRIALS_FIELD):
        load_definition(toml_path)


def test_rejects_missing_title(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path, omit=(TITLE_FIELD,))

    with pytest.raises((KeyError, ValueError), match=TITLE_FIELD):
        load_definition(toml_path)


def test_rejects_missing_cases(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path, omit=(CASES_FIELD,), with_cases=False)

    with pytest.raises((KeyError, ValueError), match=CASES_FIELD):
        load_definition(toml_path)


def test_rejects_missing_prompt(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path, omit=(PROMPT_FIELD,), with_prompt=False)

    with pytest.raises((KeyError, ValueError), match=PROMPT_FIELD):
        load_definition(toml_path)


def test_rejects_nonexistent_cases_file(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path, with_cases=False)

    with pytest.raises((FileNotFoundError, KeyError, ValueError), match=CASES_FIELD):
        load_definition(toml_path)


def test_rejects_nonexistent_prompt_file(tmp_path: Path) -> None:
    toml_path = write_eval_definition(tmp_path, with_prompt=False)

    with pytest.raises((FileNotFoundError, KeyError, ValueError), match=PROMPT_FIELD):
        load_definition(toml_path)


def test_accepts_owned_path_shapes_ci_matches_identically(tmp_path: Path) -> None:
    """An exact path and a trailing recursive glob both load.

    Both shapes are built from the source-owned alphabet and recursive suffix,
    so narrowing either contract reaches this evidence rather than passing
    beside it.
    """

    exact = "AGENTS.md"
    recursive = f"src/plugins/spec-tree/skills/merge{OWNED_PATH_RECURSIVE_SUFFIX}"
    assert OWNED_PATH_ALPHABET.fullmatch(exact)
    assert OWNED_PATH_ALPHABET.fullmatch(
        recursive.removesuffix(OWNED_PATH_RECURSIVE_SUFFIX)
    )
    accepted = (exact, recursive)
    toml_path = write_eval_definition(tmp_path, fields={OWNED_PATHS_FIELD: accepted})

    definition = load_definition(toml_path)

    assert definition.owned_paths == accepted


def test_owned_path_alphabet_excludes_every_glob_magic_character(
    tmp_path: Path,
) -> None:
    """The alphabet excludes every character the stdlib calls glob magic.

    The property evidence proves the loader honors whatever the alphabet says.
    It cannot prove the alphabet says the right thing -- a widened alphabet also
    widens the domain that evidence searches. `glob.has_magic` is an oracle
    outside this module's control, so it pins the contract the alphabet must
    keep: a path carrying a glob character is matched differently by `fnmatch`
    and by the CI provider's engine, and must never reach either.
    """

    magic = tuple(character for character in printable if glob.has_magic(character))
    assert magic

    for index, character in enumerate(magic):
        assert OWNED_PATH_ALPHABET.fullmatch(character) is None
        toml_path = write_eval_definition(
            tmp_path / str(index),
            fields={OWNED_PATHS_FIELD: (f"src{character}nested",)},
        )
        with pytest.raises(
            (FileNotFoundError, KeyError, ValueError), match=OWNED_PATHS_FIELD
        ):
            load_definition(toml_path)

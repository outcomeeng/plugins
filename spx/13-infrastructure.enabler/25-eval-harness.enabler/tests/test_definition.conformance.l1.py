"""Conformance wrappers for EvalDefinition TOML loading."""

from __future__ import annotations

from outcomeeng_evals.definition import (
    OWNED_PATH_ALPHABET,
    OWNED_PATH_RECURSIVE_SUFFIX,
)
from outcomeeng_testing.evals.factories import (
    assert_definition_accepts_trials_at_cap,
    assert_definition_applies_default_model_when_omitted,
    assert_definition_applies_default_threshold_when_omitted,
    assert_definition_applies_default_trials_when_omitted,
    assert_definition_loads_optional_ci_metadata,
    assert_definition_loads_required_fields,
    assert_definition_rejects_inherit_model,
    assert_definition_rejects_missing_cases,
    assert_definition_rejects_missing_prompt,
    assert_definition_rejects_missing_title,
    assert_definition_rejects_non_string_model,
    assert_definition_rejects_nonexistent_cases_file,
    assert_definition_rejects_nonexistent_prompt_file,
    assert_definition_rejects_trials_above_cap,
    assert_definition_rejects_trials_below_one,
    assert_definition_resolves_cases_path_relative_to_toml_directory,
    assert_definition_resolves_prompt_path_relative_to_toml_directory,
    assert_definition_uses_explicit_model_when_set,
    assert_definition_uses_explicit_threshold_when_set,
    assert_definition_uses_explicit_trials_when_set,
    assert_owned_path_alphabet_excludes_every_glob_magic_character,
    load_definition_with_owned_paths,
)


def test_loads_required_fields() -> None:
    assert_definition_loads_required_fields()


def test_resolves_cases_path_relative_to_toml_directory() -> None:
    assert_definition_resolves_cases_path_relative_to_toml_directory()


def test_resolves_prompt_path_relative_to_toml_directory() -> None:
    assert_definition_resolves_prompt_path_relative_to_toml_directory()


def test_applies_default_threshold_when_omitted() -> None:
    assert_definition_applies_default_threshold_when_omitted()


def test_applies_default_trials_when_omitted() -> None:
    assert_definition_applies_default_trials_when_omitted()


def test_applies_default_model_when_omitted() -> None:
    assert_definition_applies_default_model_when_omitted()


def test_uses_explicit_threshold_when_set() -> None:
    assert_definition_uses_explicit_threshold_when_set()


def test_uses_explicit_trials_when_set() -> None:
    assert_definition_uses_explicit_trials_when_set()


def test_loads_optional_ci_metadata() -> None:
    assert_definition_loads_optional_ci_metadata()


def test_uses_explicit_model_when_set() -> None:
    assert_definition_uses_explicit_model_when_set()


def test_rejects_inherit_model() -> None:
    assert_definition_rejects_inherit_model()


def test_rejects_non_string_model() -> None:
    assert_definition_rejects_non_string_model()


def test_accepts_trials_at_cap() -> None:
    assert_definition_accepts_trials_at_cap()


def test_rejects_trials_above_cap() -> None:
    assert_definition_rejects_trials_above_cap()


def test_rejects_trials_below_one() -> None:
    assert_definition_rejects_trials_below_one()


def test_rejects_missing_title() -> None:
    assert_definition_rejects_missing_title()


def test_rejects_missing_cases() -> None:
    assert_definition_rejects_missing_cases()


def test_rejects_missing_prompt() -> None:
    assert_definition_rejects_missing_prompt()


def test_rejects_nonexistent_cases_file() -> None:
    assert_definition_rejects_nonexistent_cases_file()


def test_rejects_nonexistent_prompt_file() -> None:
    assert_definition_rejects_nonexistent_prompt_file()


def test_accepts_owned_path_shapes_ci_matches_identically() -> None:
    exact = "AGENTS.md"
    recursive_base = "src/plugins/product-tree/skills/merge"
    recursive = f"{recursive_base}{OWNED_PATH_RECURSIVE_SUFFIX}"
    assert OWNED_PATH_ALPHABET.fullmatch(exact)
    assert OWNED_PATH_ALPHABET.fullmatch(recursive_base)

    accepted = (exact, recursive)
    definition = load_definition_with_owned_paths(accepted)

    assert definition.owned_paths == accepted


def test_owned_path_alphabet_excludes_every_glob_magic_character() -> None:
    assert_owned_path_alphabet_excludes_every_glob_magic_character()

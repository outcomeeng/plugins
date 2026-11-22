"""Conformance evidence for EvalDefinition TOML loading against its schema."""

from __future__ import annotations

import pytest

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
from outcomeeng_testing.harnesses.eval_definition_schema import (
    DefinitionShape,
    loader_accepts,
    required_table,
    schema_accepts,
    table_without,
)

EVAL_TOML_CONTRACT_SHAPES = (
    DefinitionShape("required-fields-only", required_table(), accepted=True),
    DefinitionShape("missing-title", table_without("title"), accepted=False),
    DefinitionShape("missing-cases", table_without("cases"), accepted=False),
    DefinitionShape("missing-prompt", table_without("prompt"), accepted=False),
    DefinitionShape("empty-title", required_table(title=""), accepted=False),
    DefinitionShape("explicit-model", required_table(model="opus"), accepted=True),
    DefinitionShape("inherit-model", required_table(model="inherit"), accepted=False),
    DefinitionShape("numeric-model", required_table(model=7), accepted=False),
    DefinitionShape(
        "threshold-in-range", required_table(threshold=0.85), accepted=True
    ),
    DefinitionShape(
        "threshold-above-one", required_table(threshold=1.5), accepted=False
    ),
    DefinitionShape(
        "threshold-below-zero", required_table(threshold=-0.1), accepted=False
    ),
    DefinitionShape("trials-one", required_table(trials=1), accepted=True),
    DefinitionShape("trials-at-cap", required_table(trials=100), accepted=True),
    DefinitionShape("trials-zero", required_table(trials=0), accepted=False),
    DefinitionShape("trials-above-cap", required_table(trials=101), accepted=False),
)

CI_SELECTION_METADATA_SHAPES = (
    DefinitionShape(
        "all-ci-keys",
        required_table(
            plugin_dir="dist/claude/product-tree",
            owned_paths=["AGENTS.md", "src/plugins/product-tree/skills/merge/**"],
            smoke_cases=["first-case"],
            ci_policy="manual",
        ),
        accepted=True,
    ),
    DefinitionShape("full-ci-policy", required_table(ci_policy="full"), accepted=True),
    DefinitionShape(
        "unknown-ci-policy", required_table(ci_policy="nightly"), accepted=False
    ),
    DefinitionShape("empty-plugin-dir", required_table(plugin_dir=""), accepted=False),
    DefinitionShape(
        "empty-smoke-case", required_table(smoke_cases=[""]), accepted=False
    ),
    DefinitionShape(
        "smoke-cases-not-list", required_table(smoke_cases="first-case"), accepted=False
    ),
)

OWNED_PATH_LOAD_SHAPES = (
    DefinitionShape(
        "exact-path", required_table(owned_paths=["AGENTS.md"]), accepted=True
    ),
    DefinitionShape(
        "trailing-recursive-glob",
        required_table(owned_paths=["src/plugins/product-tree/skills/merge/**"]),
        accepted=True,
    ),
    DefinitionShape(
        "star-in-body", required_table(owned_paths=["src/*.md"]), accepted=False
    ),
    DefinitionShape(
        "inner-recursive-glob",
        required_table(owned_paths=["src/**/skill"]),
        accepted=False,
    ),
    DefinitionShape(
        "doubled-recursive-glob",
        required_table(owned_paths=["src/skill/**/**"]),
        accepted=False,
    ),
    DefinitionShape(
        "space-in-body", required_table(owned_paths=["src/a b"]), accepted=False
    ),
    DefinitionShape(
        "question-mark-in-body",
        required_table(owned_paths=["src/skill?"]),
        accepted=False,
    ),
)


def _assert_schema_and_loader_agree(shape: DefinitionShape) -> None:
    assert schema_accepts(shape.table) is shape.accepted
    assert loader_accepts(shape.table) is shape.accepted


@pytest.mark.parametrize(
    "shape", EVAL_TOML_CONTRACT_SHAPES, ids=lambda shape: shape.case_id
)
def test_loader_agrees_with_schema_on_eval_toml_contract(
    shape: DefinitionShape,
) -> None:
    _assert_schema_and_loader_agree(shape)


@pytest.mark.parametrize(
    "shape", CI_SELECTION_METADATA_SHAPES, ids=lambda shape: shape.case_id
)
def test_loader_agrees_with_schema_on_ci_selection_metadata(
    shape: DefinitionShape,
) -> None:
    _assert_schema_and_loader_agree(shape)


@pytest.mark.parametrize(
    "shape", OWNED_PATH_LOAD_SHAPES, ids=lambda shape: shape.case_id
)
def test_loader_agrees_with_schema_on_owned_paths(shape: DefinitionShape) -> None:
    _assert_schema_and_loader_agree(shape)


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
    accepted = ("AGENTS.md", "src/plugins/product-tree/skills/merge/**")
    assert schema_accepts(required_table(owned_paths=list(accepted)))

    definition = load_definition_with_owned_paths(accepted)

    assert definition.owned_paths == accepted


def test_owned_path_alphabet_excludes_every_glob_magic_character() -> None:
    assert_owned_path_alphabet_excludes_every_glob_magic_character()

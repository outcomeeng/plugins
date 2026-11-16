"""Conformance evidence: the eval loader agrees with the eval definition schema."""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

import pytest

from outcomeeng_evals.definition import (
    OWNED_PATH_RECURSIVE_SUFFIX,
    OWNED_PATHS_FIELD,
    CiPolicy,
)
from outcomeeng_testing.harnesses.eval_definition import (
    ARBITRARY_MODEL,
    CI_OWNED_PATH_DIRECTORY,
    CI_OWNED_PATH_EXACT,
    CI_PLUGIN_DIR,
    CI_SMOKE_CASE,
    NON_STRING_MODEL,
    load_written_definition,
    schema_path_fields,
    schema_properties,
    schema_required_fields,
    valid_required_fields,
)


def test_loads_required_fields(tmp_path: Path) -> None:
    fields = valid_required_fields()

    loaded = load_written_definition(tmp_path, fields)

    assert loaded.error is None
    assert loaded.definition is not None
    assert loaded.definition.title == fields["title"]


def test_resolves_cases_path_relative_to_toml_directory(tmp_path: Path) -> None:
    fields = valid_required_fields()

    loaded = load_written_definition(tmp_path, fields)

    assert loaded.definition is not None
    assert (
        loaded.definition.cases_path
        == (loaded.toml_path.parent / cast(str, fields["cases"])).resolve()
    )


def test_resolves_prompt_path_relative_to_toml_directory(tmp_path: Path) -> None:
    fields = valid_required_fields()

    loaded = load_written_definition(tmp_path, fields)

    assert loaded.definition is not None
    assert (
        loaded.definition.prompt_template_path
        == (loaded.toml_path.parent / cast(str, fields["prompt"])).resolve()
    )


def test_applies_default_threshold_when_omitted(tmp_path: Path) -> None:
    loaded = load_written_definition(tmp_path, valid_required_fields())

    assert loaded.definition is not None
    assert loaded.definition.threshold == schema_properties()["threshold"]["default"]


def test_applies_default_trials_when_omitted(tmp_path: Path) -> None:
    loaded = load_written_definition(tmp_path, valid_required_fields())

    assert loaded.definition is not None
    assert loaded.definition.trials == schema_properties()["trials"]["default"]


def test_applies_default_model_when_omitted(tmp_path: Path) -> None:
    loaded = load_written_definition(tmp_path, valid_required_fields())

    assert loaded.definition is not None
    assert loaded.definition.model == schema_properties()["model"]["default"]


def test_uses_explicit_threshold_when_set(tmp_path: Path) -> None:
    explicit = schema_properties()["threshold"]["minimum"]

    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), "threshold": explicit}
    )

    assert loaded.definition is not None
    assert loaded.definition.threshold == explicit
    assert explicit != schema_properties()["threshold"]["default"]


def test_uses_explicit_trials_when_set(tmp_path: Path) -> None:
    explicit = cast(int, schema_properties()["trials"]["minimum"]) + 1

    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), "trials": explicit}
    )

    assert loaded.definition is not None
    assert loaded.definition.trials == explicit


def test_loads_optional_ci_metadata(tmp_path: Path) -> None:
    properties = schema_properties()
    non_default_policy = next(
        policy
        for policy in cast(list[str], properties["ci_policy"]["enum"])
        if policy != properties["ci_policy"]["default"]
    )
    owned_paths = [
        CI_OWNED_PATH_EXACT,
        f"{CI_OWNED_PATH_DIRECTORY}{OWNED_PATH_RECURSIVE_SUFFIX}",
    ]

    loaded = load_written_definition(
        tmp_path,
        {
            **valid_required_fields(),
            "plugin_dir": CI_PLUGIN_DIR,
            "model": ARBITRARY_MODEL,
            OWNED_PATHS_FIELD: owned_paths,
            "smoke_cases": [CI_SMOKE_CASE],
            "ci_policy": non_default_policy,
        },
    )

    assert loaded.definition is not None
    assert loaded.definition.plugin_dir == Path(CI_PLUGIN_DIR)
    assert loaded.definition.model == ARBITRARY_MODEL
    assert loaded.definition.owned_paths == tuple(owned_paths)
    assert loaded.definition.smoke_case_ids == (CI_SMOKE_CASE,)
    assert loaded.definition.ci_policy is CiPolicy(non_default_policy)


def test_uses_explicit_model_when_set(tmp_path: Path) -> None:
    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), "model": ARBITRARY_MODEL}
    )

    assert loaded.definition is not None
    assert loaded.definition.model == ARBITRARY_MODEL


def test_rejects_inherit_model(tmp_path: Path) -> None:
    excluded = cast(dict[str, str], schema_properties()["model"]["not"])["const"]

    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), "model": excluded}
    )

    assert loaded.definition is None
    assert "model" in str(loaded.error)


def test_rejects_non_string_model(tmp_path: Path) -> None:
    assert schema_properties()["model"]["type"] == "string"

    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), "model": NON_STRING_MODEL}
    )

    assert loaded.definition is None
    assert "model" in str(loaded.error)


def test_accepts_trials_at_cap(tmp_path: Path) -> None:
    cap = schema_properties()["trials"]["maximum"]

    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), "trials": cap}
    )

    assert loaded.definition is not None
    assert loaded.definition.trials == cap


def test_rejects_trials_above_cap(tmp_path: Path) -> None:
    above = cast(int, schema_properties()["trials"]["maximum"]) + 1

    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), "trials": above}
    )

    assert loaded.definition is None
    assert "trials" in str(loaded.error)


def test_rejects_trials_below_one(tmp_path: Path) -> None:
    below = cast(int, schema_properties()["trials"]["minimum"]) - 1

    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), "trials": below}
    )

    assert loaded.definition is None
    assert "trials" in str(loaded.error)


@pytest.mark.parametrize("field", schema_required_fields())
def test_rejects_missing_required_field(tmp_path: Path, field: str) -> None:
    fields = {
        name: value for name, value in valid_required_fields().items() if name != field
    }

    loaded = load_written_definition(tmp_path, fields)

    assert loaded.definition is None
    assert field in str(loaded.error)


@pytest.mark.parametrize("field", schema_path_fields())
def test_rejects_nonexistent_file_for_path_field(tmp_path: Path, field: str) -> None:
    loaded = load_written_definition(
        tmp_path, valid_required_fields(), omit_files_for=(field,)
    )

    assert loaded.definition is None
    assert field in str(loaded.error)


def test_accepts_owned_path_shapes_ci_matches_identically(tmp_path: Path) -> None:
    pattern = re.compile(
        cast(str, schema_properties()[OWNED_PATHS_FIELD]["items"]["pattern"])  # type: ignore[index]
    )
    accepted = (
        CI_OWNED_PATH_EXACT,
        f"{CI_OWNED_PATH_DIRECTORY}{OWNED_PATH_RECURSIVE_SUFFIX}",
    )
    assert all(pattern.fullmatch(path) for path in accepted)

    loaded = load_written_definition(
        tmp_path, {**valid_required_fields(), OWNED_PATHS_FIELD: list(accepted)}
    )

    assert loaded.definition is not None
    assert loaded.definition.owned_paths == accepted

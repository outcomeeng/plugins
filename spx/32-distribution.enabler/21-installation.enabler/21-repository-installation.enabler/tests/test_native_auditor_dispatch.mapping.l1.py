"""Mapping evidence for native auditor-dispatch row planning."""

import tomllib
from itertools import product
from pathlib import Path

from outcomeeng.distribution.agents import (
    AGENT_NAME_FIELD,
    NATIVE_AGENT_PLUGIN_SEPARATOR,
)
from outcomeeng.distribution.contracts import DIST_DIR_NAME, Target
from outcomeeng.distribution.installation import (
    ISOLATED_CLAUDE_CONFIG_DIRECTORY,
    ISOLATED_CODEX_HOME_DIRECTORY,
)
from outcomeeng.distribution.native_auditor_dispatch import (
    AGENTS_DIRECTORY,
    AUDITOR_PLUGIN,
    CODEX_AGENT_SUFFIX,
    CONFIGURATION_FILENAME,
    FIXTURE_DIRECTORY,
    LOADING_FILENAME,
    RESULT_FILENAME,
    SHIPPED_AUDITORS,
    native_auditor_rows,
)
from outcomeeng_testing.harnesses.installation import repository_root

FRONT_MATTER_NAME_PREFIX = f"{AGENT_NAME_FIELD}: "


def shipped_definitions(checkout: Path, target: Target, auditor: str) -> list[Path]:
    """Every file in an `agents` directory of the generated tree whose stem ends in the auditor."""
    return [
        path
        for path in (checkout / DIST_DIR_NAME / target.value / AUDITOR_PLUGIN).rglob(
            "*"
        )
        if path.is_file()
        and path.parent.name == AGENTS_DIRECTORY
        and path.stem.endswith(auditor)
    ]


def declared_name(definition: Path) -> str:
    text = definition.read_text(encoding="utf-8")
    if definition.suffix == CODEX_AGENT_SUFFIX:
        return str(tomllib.loads(text)[AGENT_NAME_FIELD])
    return next(
        line.removeprefix(FRONT_MATTER_NAME_PREFIX)
        for line in text.splitlines()
        if line.startswith(FRONT_MATTER_NAME_PREFIX)
    )


def test_rows_are_exactly_the_pairs_of_a_supported_harness_and_a_shipped_auditor(
    tmp_path: Path,
) -> None:
    checkout = repository_root()
    rows = native_auditor_rows(checkout, tmp_path / "artifacts", tmp_path / "state")

    assert {(row.target, row.auditor) for row in rows} == set(
        product(Target, SHIPPED_AUDITORS)
    )
    assert len(rows) == len(Target) * len(SHIPPED_AUDITORS)


def test_each_row_derives_identifier_and_definition_from_the_shipped_definition(
    tmp_path: Path,
) -> None:
    checkout = repository_root()
    for row in native_auditor_rows(
        checkout, tmp_path / "artifacts", tmp_path / "state"
    ):
        definitions = shipped_definitions(checkout, row.target, row.auditor)

        assert definitions == [row.shipped_definition_path]
        assert row.identifier == f"{row.target.value}-{row.auditor}"
        name = declared_name(row.shipped_definition_path)
        if row.target is Target.CLAUDE:
            assert row.native_name == (
                f"{AUDITOR_PLUGIN}{NATIVE_AGENT_PLUGIN_SEPARATOR}{name}"
            )
        else:
            assert row.native_name == name


def test_each_row_derives_artifact_and_state_paths_from_its_identifier(
    tmp_path: Path,
) -> None:
    artifacts, state = tmp_path / "artifacts", tmp_path / "state"
    rows = native_auditor_rows(
        checkout=repository_root(), artifact_root=artifacts, state_root=state
    )
    isolated_home = {
        Target.CLAUDE: ISOLATED_CLAUDE_CONFIG_DIRECTORY,
        Target.CODEX: ISOLATED_CODEX_HOME_DIRECTORY,
    }

    assert len({row.identifier for row in rows}) == len(rows)
    for row in rows:
        assert (
            row.configuration_path
            == artifacts / row.identifier / CONFIGURATION_FILENAME
        )
        assert row.loading_path == artifacts / row.identifier / LOADING_FILENAME
        assert row.result_path == artifacts / row.identifier / RESULT_FILENAME
        assert row.state_root == state / row.identifier
        assert row.native_definition_path == (
            state
            / row.identifier
            / isolated_home[row.target]
            / AGENTS_DIRECTORY
            / row.shipped_definition_path.name
        )
        assert row.fixture_path.parent == state / row.identifier / FIXTURE_DIRECTORY
        assert not row.configuration_path.is_relative_to(state)

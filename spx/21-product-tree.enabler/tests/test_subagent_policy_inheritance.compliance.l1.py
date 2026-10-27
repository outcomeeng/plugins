from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.subagent_policy_inheritance import (
    AUTHORED_AGENT_DEFINITIONS_DIRECTORY,
    CONFORMING_FIXTURE_NAME,
    FIXTURE_NAMES,
    NATIVE_FIELD_FIXTURE_NAME,
    NO_ALLOWLIST_FIXTURE_NAME,
    UNDECLARED_INHERITING_FIXTURE_NAME,
    DefinitionObservation,
    copy_fixture_definitions,
    declared_inheriting_names,
    observe_definitions,
)


def inheriting_names(
    observations: tuple[DefinitionObservation, ...],
) -> frozenset[str]:
    """Names with a tools allowlist and no native permission field in a rendering."""
    return frozenset(
        observation.name
        for observation in observations
        if any(
            rendering.declares_tools_allowlist
            and not rendering.declares_native_permission_field
            for rendering in observation.renderings.values()
        )
    )


def test_authored_definitions_inheriting_policy_are_exactly_the_declared_set() -> None:
    declared = declared_inheriting_names()
    inheriting = inheriting_names(
        observe_definitions(AUTHORED_AGENT_DEFINITIONS_DIRECTORY)
    )

    assert declared
    assert inheriting - declared == frozenset()
    assert declared - inheriting == frozenset()


def test_an_undeclared_definition_inheriting_policy_is_outside_the_declared_set(
    tmp_path: Path,
) -> None:
    observations = observe_definitions(
        copy_fixture_definitions(tmp_path, FIXTURE_NAMES)
    )
    declared = frozenset({CONFORMING_FIXTURE_NAME})

    assert inheriting_names(observations) - declared == frozenset(
        {UNDECLARED_INHERITING_FIXTURE_NAME}
    )


def test_a_declared_definition_with_a_native_field_in_every_rendering_does_not_inherit(
    tmp_path: Path,
) -> None:
    observations = observe_definitions(
        copy_fixture_definitions(tmp_path, FIXTURE_NAMES)
    )
    declared = frozenset({CONFORMING_FIXTURE_NAME, NATIVE_FIELD_FIXTURE_NAME})

    assert declared - inheriting_names(observations) == frozenset(
        {NATIVE_FIELD_FIXTURE_NAME}
    )


def test_a_conforming_definition_and_a_definition_without_an_allowlist_are_accepted(
    tmp_path: Path,
) -> None:
    observations = observe_definitions(
        copy_fixture_definitions(
            tmp_path, (CONFORMING_FIXTURE_NAME, NO_ALLOWLIST_FIXTURE_NAME)
        )
    )
    declared = frozenset({CONFORMING_FIXTURE_NAME})

    assert inheriting_names(observations) == declared

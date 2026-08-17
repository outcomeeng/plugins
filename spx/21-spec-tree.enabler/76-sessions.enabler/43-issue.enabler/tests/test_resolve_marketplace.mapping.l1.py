"""Mapping tests for the /issue marketplace resolver script."""

from __future__ import annotations

from outcomeeng_testing.generators.resolve_marketplace import (
    ResolutionCase,
    registration_field_domain,
)
from outcomeeng_testing.harnesses.resolve_marketplace import (
    RESOLVER,
    none_available_message,
    run_resolver,
)

import pytest

REGISTRATION_FIELD_DOMAIN = registration_field_domain("/registered")


@pytest.mark.parametrize(
    "case",
    REGISTRATION_FIELD_DOMAIN,
    ids=[case.label for case in REGISTRATION_FIELD_DOMAIN],
)
def test_registration_fields_map_to_the_resolved_checkout_path(
    case: ResolutionCase,
) -> None:
    result = run_resolver(case.payload, runtime=case.runtime)

    if case.expected_path is None:
        assert result.returncode == RESOLVER.EXIT_MARKETPLACE_NOT_FOUND
        assert result.stdout == ""
        assert none_available_message() in result.stderr
    else:
        assert result.returncode == 0
        assert result.stdout == f"{case.expected_path}\n"
        assert result.stderr == ""


def test_same_name_entries_map_to_the_first_resolvable_one() -> None:
    resolvable = "/registered/second-entry"
    payload = [
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
        },
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
            RESOLVER.PATH_FIELD: resolvable,
        },
    ]

    result = run_resolver(payload, runtime=RESOLVER.RUNTIME_CLAUDE)

    assert result.returncode == 0
    assert result.stdout == f"{resolvable}\n"


def test_omitted_name_maps_to_the_default_marketplace() -> None:
    registered_path = "/registered/default-marketplace"
    payload = [
        {
            RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME,
            RESOLVER.SOURCE_FIELD: RESOLVER.CLAUDE_DIRECTORY_SOURCE,
            RESOLVER.PATH_FIELD: registered_path,
        }
    ]

    result = run_resolver(payload, runtime=RESOLVER.RUNTIME_CLAUDE, name=None)

    assert result.returncode == 0
    assert result.stdout == f"{registered_path}\n"


def test_another_marketplace_name_maps_to_none_available() -> None:
    payload = {
        RESOLVER.MARKETPLACES_FIELD: [
            {
                RESOLVER.NAME_FIELD: "git-marketplace",
                RESOLVER.ROOT_FIELD: "/registered/git-cache",
                RESOLVER.MARKETPLACE_SOURCE_FIELD: {
                    RESOLVER.SOURCE_TYPE_FIELD: "git",
                    RESOLVER.SOURCE_FIELD: "https://example.invalid/plugins.git",
                },
            }
        ]
    }

    result = run_resolver(payload, runtime=RESOLVER.RUNTIME_CODEX)

    assert result.returncode == RESOLVER.EXIT_MARKETPLACE_NOT_FOUND
    assert result.stdout == ""
    assert none_available_message() in result.stderr

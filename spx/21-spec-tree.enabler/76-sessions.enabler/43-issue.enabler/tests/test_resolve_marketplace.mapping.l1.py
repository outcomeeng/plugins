"""Mapping tests for the /issue marketplace resolver script."""

from __future__ import annotations

import pytest

from outcomeeng_testing.generators.resolve_marketplace import (
    ResolutionCase,
    SelectionCase,
    entry_selection_domain,
    registration_field_domain,
)
from outcomeeng_testing.harnesses.resolve_marketplace import (
    RESOLVER,
    none_available_message,
    run_resolver,
)

REGISTRATION_FIELD_DOMAIN = registration_field_domain("/registered")
ENTRY_SELECTION_DOMAIN = entry_selection_domain("/registered")


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
        assert (
            none_available_message(
                name=RESOLVER.DEFAULT_MARKETPLACE_NAME, runtime=case.runtime
            )
            in result.stderr
        )
    else:
        assert result.returncode == 0
        assert result.stdout == f"{case.expected_path}\n"
        assert result.stderr == ""


@pytest.mark.parametrize(
    "case",
    ENTRY_SELECTION_DOMAIN,
    ids=[case.label for case in ENTRY_SELECTION_DOMAIN],
)
def test_requested_name_maps_to_the_first_resolvable_entry(
    case: SelectionCase,
) -> None:
    result = run_resolver(
        case.payload, runtime=case.runtime, name=case.requested_name
    )

    if case.expected_path is None:
        assert result.returncode == RESOLVER.EXIT_MARKETPLACE_NOT_FOUND
        assert result.stdout == ""
    else:
        assert result.returncode == 0
        assert result.stdout == f"{case.expected_path}\n"
        assert result.stderr == ""

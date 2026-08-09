import pytest

from outcomeeng_testing.harnesses.contribution_targeting import (
    CHECKOUT_VIEW,
    PARENT,
    Responses,
    account_lookups,
    checkout_response,
    permission_key,
    permission_response,
    resolve_with,
)

CLASSIFICATIONS = [
    (False, "ADMIN", "controlled"),
    (False, "MAINTAIN", "controlled"),
    (False, "WRITE", "controlled"),
    (True, "ADMIN", "controlled"),
    (True, "MAINTAIN", "controlled"),
    (True, "WRITE", "controlled"),
    (True, "READ", "parent-contribution"),
    (True, "NONE", "parent-contribution"),
    (False, "READ", "fork-absent"),
    (False, "NONE", "fork-absent"),
    (False, "TRIAGE", "blocked"),
    (True, "TRIAGE", "blocked"),
]


@pytest.mark.parametrize(("is_fork", "permission", "expected"), CLASSIFICATIONS)
def test_fork_state_and_permission_map_to_one_classification(
    is_fork: bool, permission: str, expected: str
) -> None:
    responses: Responses = {
        CHECKOUT_VIEW: checkout_response(is_fork),
        permission_key(PARENT): permission_response(permission),
        **account_lookups(),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification == expected

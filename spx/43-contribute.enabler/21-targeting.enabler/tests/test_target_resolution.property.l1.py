"""Level-1 property evidence for permissions outside the resolver's buckets."""

from __future__ import annotations

from outcomeeng_testing.harnesses.contribution_targeting import (
    checkout_view_key,
    PARENT,
    Responses,
    account_lookups,
    checkout_response,
    permission_key,
    permission_response,
    resolve_with,
    run_unrecognized_permission_property,
)


def test_any_permission_outside_both_buckets_blocks_the_target() -> None:
    def check(is_fork: bool, permission: str) -> None:
        responses: Responses = {
            checkout_view_key(): checkout_response(is_fork),
            permission_key(PARENT): permission_response(permission),
            **account_lookups(),
        }

        resolution, _ = resolve_with(responses)

        assert resolution.classification == "blocked"

    run_unrecognized_permission_property(check)

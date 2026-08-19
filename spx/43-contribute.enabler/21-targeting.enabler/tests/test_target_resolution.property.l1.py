"""Level-1 property evidence for permissions outside the resolver's buckets."""

from __future__ import annotations

from outcomeeng_testing.harnesses.contribution_targeting import (
    PARENT,
    Responses,
    head_search_lookups,
    checkout_lookups,
    load_resolver,
    permission_key,
    permission_response,
    resolve_with,
    run_unrecognized_permission_property,
)

_RESOLVER = load_resolver()


def test_any_permission_outside_both_buckets_blocks_the_target() -> None:
    def check(is_fork: bool, permission: str) -> None:
        responses: Responses = {
            **checkout_lookups(is_fork),
            permission_key(PARENT): permission_response(permission),
            **head_search_lookups(0),
        }

        resolution, _ = resolve_with(responses)

        assert resolution.classification is _RESOLVER.Classification.BLOCKED

    run_unrecognized_permission_property(check)

import pytest

from outcomeeng_testing.harnesses.contribution_targeting import (
    checkout_view_key,
    PARENT,
    Responses,
    account_lookups,
    checkout_response,
    load_resolver,
    permission_key,
    permission_response,
    resolve_with,
)

# `gh` reports a permission the resolver either controls or contributes to. Both
# sets are the resolver's own and finite, which is what makes this domain a
# mapping. Every value outside them is an open remainder with no finite
# enumeration, so it is proven by generator in
# `test_target_resolution.property.l1.py` rather than by a hand-picked example
# here.
#
# The bucket membership is imported rather than restated. It is a value the spec
# tree declares and the resolver complies with, so every oracle for that
# agreement is a second declaration: a copy here would compare the resolver to
# a transcription and
# hold for whatever the transcription said. What this file verifies is the
# behavior the value governs — which classification each bucket produces under
# each fork state — and the agreement itself reaches audit.
_RESOLVER = load_resolver()


def classifications() -> list[tuple[bool, str, object]]:
    """Every fork state paired with every permission bucket the resolver names."""
    cases: list[tuple[bool, str, object]] = []
    for is_fork in (False, True):
        for permission in sorted(_RESOLVER.CONTROLLED_PERMISSIONS):
            cases.append((is_fork, permission, _RESOLVER.Classification.CONTROLLED))
        for permission in sorted(_RESOLVER.CONTRIBUTOR_PERMISSIONS):
            cases.append(
                (
                    is_fork,
                    permission,
                    _RESOLVER.Classification.PARENT_CONTRIBUTION
                    if is_fork
                    else _RESOLVER.Classification.FORK_ABSENT,
                )
            )
    return cases


CLASSIFICATIONS = classifications()


def test_the_permission_buckets_partition_the_values_they_name() -> None:
    controlled = _RESOLVER.CONTROLLED_PERMISSIONS
    contributor = _RESOLVER.CONTRIBUTOR_PERMISSIONS

    assert not (controlled & contributor)
    assert controlled and contributor


@pytest.mark.parametrize(("is_fork", "permission", "expected"), CLASSIFICATIONS)
def test_fork_state_and_permission_map_to_one_classification(
    is_fork: bool, permission: str, expected: object
) -> None:
    responses: Responses = {
        checkout_view_key(): checkout_response(is_fork),
        permission_key(PARENT): permission_response(permission),
        **account_lookups(),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification == expected

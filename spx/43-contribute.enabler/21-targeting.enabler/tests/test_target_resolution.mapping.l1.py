import pytest

from outcomeeng_testing.harnesses.contribution_targeting import (
    PARENT,
    Responses,
    checkout_response,
    checkout_view_key,
    head_search_lookups,
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
# a transcription and hold for whatever the transcription said. What this file
# verifies is the behavior the value governs — which classification each bucket
# produces under each fork state and head-search result — and the agreement
# itself reaches audit.
_RESOLVER = load_resolver()

# How many forks of the base the search finds. A fork checkout supplies its own
# head and never searches, so the count applies only to a non-fork checkout.
MATCH_COUNTS = (0, 1, 2)


def classifications() -> list[tuple[bool, str, int, object]]:
    """Every fork state and head-search result paired with every permission bucket."""
    cases: list[tuple[bool, str, int, object]] = []
    for is_fork in (False, True):
        for permission in sorted(_RESOLVER.CONTROLLED_PERMISSIONS):
            cases.append((is_fork, permission, 0, _RESOLVER.Classification.CONTROLLED))
        for permission in sorted(_RESOLVER.CONTRIBUTOR_PERMISSIONS):
            if is_fork:
                cases.append(
                    (
                        is_fork,
                        permission,
                        0,
                        _RESOLVER.Classification.UPSTREAM_CONTRIBUTION,
                    )
                )
                continue
            for matches in MATCH_COUNTS:
                cases.append((is_fork, permission, matches, expected_for(matches)))
    return cases


def expected_for(matches: int) -> object:
    """The classification a non-fork checkout reaches for `matches` forks found."""
    if matches == 0:
        return _RESOLVER.Classification.FORK_ABSENT
    if matches == 1:
        return _RESOLVER.Classification.UPSTREAM_CONTRIBUTION
    return _RESOLVER.Classification.HEAD_AMBIGUOUS


CLASSIFICATIONS = classifications()


def test_the_permission_buckets_partition_the_values_they_name() -> None:
    controlled = _RESOLVER.CONTROLLED_PERMISSIONS
    contributor = _RESOLVER.CONTRIBUTOR_PERMISSIONS

    assert not (controlled & contributor)
    assert controlled and contributor


@pytest.mark.parametrize(
    ("is_fork", "permission", "matches", "expected"), CLASSIFICATIONS
)
def test_fork_state_permission_and_head_search_map_to_one_classification(
    is_fork: bool, permission: str, matches: int, expected: object
) -> None:
    responses: Responses = {
        checkout_view_key(): checkout_response(is_fork),
        permission_key(PARENT): permission_response(permission),
        **head_search_lookups(matches),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification == expected


@pytest.mark.parametrize("matches", MATCH_COUNTS)
def test_the_head_a_search_reports_is_the_head_resolution_carries(
    matches: int,
) -> None:
    """One match becomes the head; every other count leaves none to carry."""
    responses: Responses = {
        checkout_view_key(): checkout_response(False),
        permission_key(PARENT): permission_response("READ"),
        **head_search_lookups(matches),
    }

    resolution, _ = resolve_with(responses)

    assert len(resolution.fork_matches) == matches
    assert resolution.head == (resolution.fork_matches[0] if matches == 1 else None)

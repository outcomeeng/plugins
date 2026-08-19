"""Level-1 mapping evidence for how a fork listing maps to the base it forked."""

import pytest

from outcomeeng_testing.harnesses.contribution_targeting import (
    OWNERS,
    PARENT,
    Responses,
    account_lookups,
    checkout_lookups,
    fork_list_key,
    fork_list_response,
    load_resolver,
    permission_key,
    permission_response,
    resolve_with,
)

_RESOLVER = load_resolver()

# How one owner's listing can report the repository a fork came from. GitHub
# preserves a repository's case and matches it without one, so every spelling
# that differs from the base only in case names the same repository. A spelling
# that differs in a character is a different repository and never matches.
#
# The base itself is `someone/example`; each entry pairs the parent spelling a
# listing reports with whether it names that base.
SOURCE_SPELLINGS: tuple[tuple[str, bool], ...] = (
    ("someone/example", True),
    ("Someone/Example", True),
    ("SOMEONE/EXAMPLE", True),
    ("someone/EXAMPLE", True),
    ("someone/examples", False),
    ("someones/example", False),
    ("other/example", False),
)


def responses_for(source: str) -> Responses:
    """A non-fork checkout of the base, with one owner holding a fork of `source`."""
    lookups: Responses = dict(account_lookups())
    lookups[fork_list_key(OWNERS[0])] = fork_list_response(
        [(f"{OWNERS[0]}/example", source)]
    )
    lookups[fork_list_key(OWNERS[1])] = fork_list_response([])
    return {
        **checkout_lookups(False),
        permission_key(PARENT): permission_response("READ"),
        **lookups,
    }


def test_the_base_under_test_is_the_spelling_the_cases_vary() -> None:
    """An unrelated base would make every case below vacuously false."""
    assert PARENT == "someone/example"


@pytest.mark.parametrize(("source", "matches"), SOURCE_SPELLINGS)
def test_a_reported_source_maps_to_whether_it_names_the_base(
    source: str, matches: bool
) -> None:
    resolution, _ = resolve_with(responses_for(source))

    found = list(resolution.fork_matches)

    assert found == ([f"{OWNERS[0]}/example"] if matches else [])
    assert resolution.classification is (
        _RESOLVER.Classification.UPSTREAM_CONTRIBUTION
        if matches
        else _RESOLVER.Classification.FORK_ABSENT
    )


def test_a_listing_entry_reporting_no_source_matches_nothing() -> None:
    """`gh` reports a null parent for an entry it cannot resolve one for."""
    lookups: Responses = dict(account_lookups())
    lookups[fork_list_key(OWNERS[0])] = (0, '[{"nameWithOwner": "operator/x"}]', "")
    lookups[fork_list_key(OWNERS[1])] = fork_list_response([])
    responses: Responses = {
        **checkout_lookups(False),
        permission_key(PARENT): permission_response("READ"),
        **lookups,
    }

    resolution, _ = resolve_with(responses)

    assert list(resolution.fork_matches) == []
    assert resolution.classification is _RESOLVER.Classification.FORK_ABSENT

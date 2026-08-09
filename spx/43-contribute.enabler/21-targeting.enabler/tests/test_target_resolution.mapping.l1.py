import pytest

from outcomeeng_testing.harnesses.contribution_targeting import (
    CHECKOUT_VIEW,
    PARENT,
    Responses,
    account_lookups,
    checkout_response,
    load_resolver,
    permission_key,
    permission_response,
    resolve_with,
)

# `gh` reports a permission the resolver either controls, contributes to, or
# recognizes as neither. The first two sets are the resolver's own; the third is
# every other value `gh` can return, standing in for the open remainder.
#
# The bucket membership is imported rather than restated. It is a value the spec
# tree declares and the resolver complies with, so under
# `spx/12-shipped-scripting.adr.md` every oracle for that agreement is a second
# declaration: a copy here would compare the resolver to a transcription and
# hold for whatever the transcription said. What this file verifies is the
# behavior the value governs — which classification each bucket produces under
# each fork state — and the agreement itself reaches audit.
_RESOLVER = load_resolver()
UNRECOGNIZED_PERMISSION = "TRIAGE"


def classifications() -> list[tuple[bool, str, str]]:
    """Every fork state paired with every permission bucket the resolver names."""
    cases: list[tuple[bool, str, str]] = []
    for is_fork in (False, True):
        for permission in sorted(_RESOLVER.CONTROLLED_PERMISSIONS):
            cases.append((is_fork, permission, "controlled"))
        for permission in sorted(_RESOLVER.CONTRIBUTOR_PERMISSIONS):
            cases.append(
                (
                    is_fork,
                    permission,
                    "parent-contribution" if is_fork else "fork-absent",
                )
            )
        cases.append((is_fork, UNRECOGNIZED_PERMISSION, "blocked"))
    return cases


CLASSIFICATIONS = classifications()


def test_the_permission_buckets_partition_the_values_they_name() -> None:
    controlled = _RESOLVER.CONTROLLED_PERMISSIONS
    contributor = _RESOLVER.CONTRIBUTOR_PERMISSIONS

    assert not (controlled & contributor)
    assert controlled and contributor
    assert UNRECOGNIZED_PERMISSION not in (controlled | contributor)


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

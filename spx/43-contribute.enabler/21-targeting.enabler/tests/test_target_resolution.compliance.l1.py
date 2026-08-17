import pytest

from outcomeeng_testing.harnesses.contribution_targeting import (
    FORK,
    OWNERS,
    PARENT,
    Responses,
    account_key,
    checkout_response,
    checkout_view_key,
    command_failure,
    command_output,
    fork_list_key,
    full_fork_page,
    head_search_lookups,
    load_resolver,
    organizations_key,
    orphan_fork_response,
    permission_key,
    permission_response,
    resolve_with,
)

_RESOLVER = load_resolver()


def test_an_absent_permission_field_yields_no_permission_class() -> None:
    responses: Responses = {
        checkout_view_key(): checkout_response(True),
        permission_key(PARENT): permission_response(None),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification is _RESOLVER.Classification.BLOCKED
    assert resolution.permission is None


def test_no_signal_outside_gh_is_consulted_for_permission() -> None:
    responses: Responses = {
        checkout_view_key(): checkout_response(True),
        permission_key(PARENT): permission_response(None),
    }

    _, runner = resolve_with(responses)

    assert [command for command in runner.commands if command[:1] != ("gh",)] == []


def test_a_failed_permission_read_blocks_and_keeps_the_gh_error() -> None:
    responses: Responses = {
        checkout_view_key(): checkout_response(True),
        permission_key(PARENT): (1, "", "HTTP 404: Not Found"),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification is _RESOLVER.Classification.BLOCKED
    assert "HTTP 404: Not Found" in resolution.detail


def test_an_unavailable_gh_blocks_before_reading_permission() -> None:
    responses: Responses = {checkout_view_key(): (127, "", "gh: command not found")}

    resolution, runner = resolve_with(responses)

    assert resolution.classification is _RESOLVER.Classification.BLOCKED
    assert runner.commands == [checkout_view_key()]


def test_absence_of_a_head_is_searched_for_never_inferred() -> None:
    """A non-fork checkout is where the head must be found, not ruled out.

    Reporting absence from `isFork` alone is the defect: an operator working from
    a clone of the base holds the fork elsewhere. The search must reach every
    owner before absence is claimed.
    """
    responses: Responses = {
        checkout_view_key(): checkout_response(False),
        permission_key(PARENT): permission_response("READ"),
        **head_search_lookups(0),
    }

    resolution, runner = resolve_with(responses)

    assert resolution.classification is _RESOLVER.Classification.FORK_ABSENT
    searched = [
        command for command in runner.commands if command[:3] == ("gh", "repo", "list")
    ]
    assert [fork_list_key(owner) for owner in OWNERS] == searched


# Each way the search can fail to cover its domain. Absence claimed from any of
# them would be inference, so each blocks instead.
#
# Every lookup fails in four forms, not one: the command exits non-zero, it exits
# zero carrying output no parser accepts, it exits zero carrying a JSON shape the
# resolver does not expect, or it exits zero carrying a payload without the field
# the resolver reads. A table covering only the non-zero form leaves the three
# quiet ones — the ones a green exit code hides — unexercised.
INCOMPLETE_SEARCHES: tuple[tuple[str, Responses], ...] = (
    (
        "the authenticated account read fails",
        {account_key(): command_failure("HTTP 401: Bad credentials")},
    ),
    (
        "the authenticated account read returns unparseable output",
        {account_key(): command_output("<html>502 Bad Gateway</html>")},
    ),
    (
        "the authenticated account read returns a list",
        {account_key(): command_output("[]")},
    ),
    (
        "the authenticated account read omits the login",
        {account_key(): command_output("{}")},
    ),
    (
        "the organization listing fails",
        {organizations_key(): command_failure("HTTP 502: Bad gateway")},
    ),
    (
        "the organization listing returns unparseable output",
        {organizations_key(): command_output("<html>502 Bad Gateway</html>")},
    ),
    (
        "the organization listing returns an object",
        {organizations_key(): command_output("{}")},
    ),
    (
        "one owner's fork listing fails",
        {fork_list_key(OWNERS[1]): command_failure("HTTP 403: Forbidden")},
    ),
    (
        "one owner's fork listing returns unparseable output",
        {fork_list_key(OWNERS[1]): command_output("<html>403 Forbidden</html>")},
    ),
    (
        "one owner's fork listing returns an object",
        {fork_list_key(OWNERS[1]): command_output("{}")},
    ),
    (
        "one owner's fork listing fills the page",
        {fork_list_key(OWNERS[0]): full_fork_page(OWNERS[0])},
    ),
)


@pytest.mark.parametrize(
    ("condition", "override"),
    INCOMPLETE_SEARCHES,
    ids=[condition for condition, _ in INCOMPLETE_SEARCHES],
)
def test_a_search_that_did_not_cover_its_domain_blocks_instead_of_reporting_absence(
    condition: str, override: Responses
) -> None:
    """Absence is what the search establishes, so an incomplete search establishes none.

    Every case below would otherwise reach `fork-absent`: each leaves the resolver
    holding zero matches, which is the same state a completed search of an operator
    who holds no fork produces. Reporting absence there hands back a `gh repo fork`
    command GitHub rejects whenever the unread account already holds one.
    """
    responses: Responses = {
        checkout_view_key(): checkout_response(False),
        permission_key(PARENT): permission_response("READ"),
        **head_search_lookups(0),
        **override,
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification is _RESOLVER.Classification.BLOCKED
    assert resolution.classification is not _RESOLVER.Classification.FORK_ABSENT
    assert resolution.head is None
    # A block that names nothing leaves the operator with the same dead end
    # `fork-absent` would have handed them, minus the wrong command.
    assert resolution.detail


def test_a_full_fork_page_blocks_even_though_its_entries_match_nothing() -> None:
    """Page length decides, not the entries a truncated page happens to carry.

    The full page holds forks of an unrelated repository, so a resolver reading
    contents alone would find no match and call the fork absent. The page being
    full is the whole signal: the match may sit on the page that was never read.
    """
    responses: Responses = {
        checkout_view_key(): checkout_response(False),
        permission_key(PARENT): permission_response("READ"),
        **head_search_lookups(0),
        fork_list_key(OWNERS[0]): full_fork_page(OWNERS[0]),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification is _RESOLVER.Classification.BLOCKED
    assert str(_RESOLVER.FORK_LIST_LIMIT) in resolution.detail


def test_several_forks_are_named_and_none_is_selected() -> None:
    """Choosing among them is the operator's, so resolution carries no head."""
    responses: Responses = {
        checkout_view_key(): checkout_response(False),
        permission_key(PARENT): permission_response("READ"),
        **head_search_lookups(2),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification is _RESOLVER.Classification.HEAD_AMBIGUOUS
    assert resolution.head is None
    assert len(resolution.fork_matches) == 2
    for match in resolution.fork_matches:
        assert match in resolution.detail


def test_a_fork_reported_without_a_parent_blocks() -> None:
    # The permission read on the fork itself succeeds with ADMIN, which is what a
    # real gh reports for the operator's own fork. Without that response the test
    # would pass on the runner's unconfigured-command failure rather than on the
    # resolver detecting the orphaned fork.
    responses: Responses = {
        checkout_view_key(): orphan_fork_response(),
        permission_key(FORK): permission_response("ADMIN"),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification is _RESOLVER.Classification.BLOCKED
    assert resolution.permission is None
    assert resolution.base is None

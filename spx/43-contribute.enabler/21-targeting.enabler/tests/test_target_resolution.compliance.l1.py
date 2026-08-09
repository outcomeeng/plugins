from outcomeeng_testing.harnesses.contribution_targeting import (
    CHECKOUT_VIEW,
    FORK,
    PARENT,
    Responses,
    checkout_response,
    orphan_fork_response,
    permission_key,
    permission_response,
    resolve_with,
)


def test_an_absent_permission_field_yields_no_permission_class() -> None:
    responses: Responses = {
        CHECKOUT_VIEW: checkout_response(True),
        permission_key(PARENT): permission_response(None),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification == "blocked"
    assert resolution.permission is None


def test_no_signal_outside_gh_is_consulted_for_permission() -> None:
    responses: Responses = {
        CHECKOUT_VIEW: checkout_response(True),
        permission_key(PARENT): permission_response(None),
    }

    _, runner = resolve_with(responses)

    assert [command for command in runner.commands if command[:1] != ("gh",)] == []


def test_a_failed_permission_read_blocks_and_keeps_the_gh_error() -> None:
    responses: Responses = {
        CHECKOUT_VIEW: checkout_response(True),
        permission_key(PARENT): (1, "", "HTTP 404: Not Found"),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification == "blocked"
    assert "HTTP 404: Not Found" in resolution.detail


def test_an_unavailable_gh_blocks_before_reading_permission() -> None:
    responses: Responses = {CHECKOUT_VIEW: (127, "", "gh: command not found")}

    resolution, runner = resolve_with(responses)

    assert resolution.classification == "blocked"
    assert runner.commands == [CHECKOUT_VIEW]


def test_a_fork_reported_without_a_parent_blocks() -> None:
    # The permission read on the fork itself succeeds with ADMIN, which is what a
    # real gh reports for the operator's own fork. Without that response the test
    # would pass on the runner's unconfigured-command failure rather than on the
    # resolver detecting the orphaned fork.
    responses: Responses = {
        CHECKOUT_VIEW: orphan_fork_response(),
        permission_key(FORK): permission_response("ADMIN"),
    }

    resolution, _ = resolve_with(responses)

    assert resolution.classification == "blocked"
    assert resolution.permission is None
    assert resolution.base is None

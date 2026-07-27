"""Scenario evidence for direct marketplace push."""

from outcomeeng.distribution.push import GIT_PUSH_COMMAND, GIT_TOOL
from outcomeeng_testing.harnesses.push import (
    observe_explicit_ref_push,
    observe_failed_push,
    observe_help_push,
)


def test_push_forwards_leading_flags_and_explicit_refspec_verbatim() -> None:
    observation = observe_explicit_ref_push()

    assert observation.parsed_args == observation.supplied_args
    assert observation.calls == ((*GIT_PUSH_COMMAND, *observation.supplied_args),)
    assert observation.queries == (GIT_TOOL,)


def test_push_propagates_git_exit_without_installation_operations() -> None:
    observation = observe_failed_push()

    assert observation.exit_code == observation.runner_exit_code
    assert observation.calls == ((*GIT_PUSH_COMMAND, *observation.supplied_args),)
    assert len(observation.calls) == 1


def test_git_help_is_forwarded_after_only_the_git_probe() -> None:
    observation = observe_help_push()

    assert observation.exit_code == observation.runner_exit_code
    assert observation.queries == (GIT_TOOL,)
    assert observation.calls == ((*GIT_PUSH_COMMAND, *observation.supplied_args),)

"""Dependency-boundary evidence for direct marketplace push."""

from outcomeeng.distribution.push import GIT_PUSH_COMMAND, GIT_TOOL
from outcomeeng_testing.harnesses.push import observe_bare_push, observe_missing_git


def test_push_requires_only_git_before_publication() -> None:
    observation = observe_bare_push()

    assert observation.queries == (GIT_TOOL,)
    assert observation.calls == (GIT_PUSH_COMMAND,)
    assert observation.exit_code == observation.runner_exit_code


def test_missing_git_fails_before_any_publication_command() -> None:
    observation = observe_missing_git()

    assert observation.exit_code != 0
    assert observation.queries == (GIT_TOOL,)
    assert observation.calls == ()
    assert GIT_TOOL in observation.stderr

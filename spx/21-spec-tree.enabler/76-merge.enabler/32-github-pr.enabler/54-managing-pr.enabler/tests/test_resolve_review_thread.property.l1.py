"""Property evidence for malformed review-thread resolver arguments."""

from __future__ import annotations

from hypothesis import given

from outcomeeng_testing.generators.review_thread_resolver import (
    malformed_resolver_argvs,
)
from outcomeeng_testing.harnesses.review_thread_resolver import (
    RESOLVER,
    completed,
    resolver_property,
    run_resolver,
)


@resolver_property
@given(argv=malformed_resolver_argvs())
def test_malformed_inputs_fail_before_github_calls(argv: tuple[str, ...]) -> None:
    run = run_resolver(
        argv,
        lambda command, _kwargs: completed(command, returncode=97),
    )

    assert run.returncode == RESOLVER.ResolverExitCode.INVALID_INPUT
    assert run.stderr
    assert run.interactions == ()

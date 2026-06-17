"""Property tests for the re-exported ``branch_slug`` function.

Covers the Property clauses on ``branch_slug`` in
``../manage-thread-store.md``:

- idempotence: ``branch_slug(branch_slug(x)) == branch_slug(x)``
- injectivity: distinct branch names produce distinct slugs
- path-safety: no ``/``, no ``.``/``..`` whole-segment values
- length-bound: every slug is at most ``BRANCH_SLUG_MAX_LENGTH`` chars

The symbol-identity assertion (Compliance) lives in
``test_thread_store.compliance.l1.py`` — one evidence type per file.
"""

from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.thread_store import load_branch_slug_module


def valid_branch_names() -> st.SearchStrategy[str]:
    """Generate strings that resemble git branch names.

    Git's ref-format rules constrain real branch names; the slug
    function is tested over the wider set of strings the function may
    legitimately encounter (synthetic identifiers, draft branches, and
    canonical refs). The strategy excludes the empty string because the
    slug function does not define a slug for an empty input.
    """
    return st.text(
        alphabet=st.characters(
            min_codepoint=0x20,
            max_codepoint=0x7E,
            exclude_characters=("\x00",),
        ),
        min_size=1,
        max_size=256,
    )


def long_branch_names() -> st.SearchStrategy[str]:
    """Generate branch names that exceed ``BRANCH_SLUG_MAX_LENGTH`` (64).

    Long inputs exercise the truncation-plus-digest branch of the slug
    function. Two inputs that share a 64-character prefix would collide
    after truncation without the ``--<sha8>`` disambiguator; the
    injectivity property must hold under that branch as well.
    """
    return st.text(
        alphabet=st.characters(
            min_codepoint=0x20,
            max_codepoint=0x7E,
            exclude_characters=("\x00",),
        ),
        min_size=80,
        max_size=512,
    )


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(name=valid_branch_names())
def test_branch_slug_is_idempotent(name: str) -> None:
    branch_slug = load_branch_slug_module().branch_slug
    once = branch_slug(name)
    twice = branch_slug(once)
    assert twice == once


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(
    pair=st.tuples(valid_branch_names(), valid_branch_names()).filter(
        lambda p: p[0] != p[1]
    )
)
def test_branch_slug_is_injective(pair: tuple[str, str]) -> None:
    branch_slug = load_branch_slug_module().branch_slug
    a, b = pair
    assert branch_slug(a) != branch_slug(b)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(
    pair=st.tuples(long_branch_names(), long_branch_names()).filter(
        lambda p: p[0] != p[1]
    )
)
def test_branch_slug_is_injective_on_long_inputs(pair: tuple[str, str]) -> None:
    """Distinct branch names whose prefixes collide after truncation must
    still produce distinct slugs.

    Long inputs exercise the truncation-plus-digest branch. The
    ``--<sha8>`` suffix is the disambiguator; the property would fail
    without it for any pair of inputs that share a 64-character prefix.
    """
    branch_slug = load_branch_slug_module().branch_slug
    a, b = pair
    assert branch_slug(a) != branch_slug(b)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(name=valid_branch_names())
def test_branch_slug_output_is_path_safe(name: str) -> None:
    branch_slug = load_branch_slug_module().branch_slug
    slug = branch_slug(name)
    assert "/" not in slug
    # A slug whose entire value resolves a parent or current directory
    # cannot be used as a path segment by any backend.
    assert slug not in (".", "..")
    # Internal `.` characters are fine (they cannot resolve a parent
    # segment by themselves); the rule is about whole-segment values.


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(name=valid_branch_names())
def test_branch_slug_output_length_is_bounded(name: str) -> None:
    branch_slug_module = load_branch_slug_module()
    branch_slug = branch_slug_module.branch_slug
    max_length = branch_slug_module.BRANCH_SLUG_MAX_LENGTH
    slug = branch_slug(name)
    assert len(slug) <= max_length

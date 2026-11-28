"""Compliance evidence for the Hypothesis profiles every pytest run registers."""

from __future__ import annotations

import inspect

import pytest
from hypothesis import settings

from outcomeeng_testing.harnesses.hypothesis_profiles import (
    loaded_profile,
    profile_loaded,
    unrouted_example_counts,
)
from outcomeeng_testing.hypothesis_profiles import (
    FULL_MAX_EXAMPLES,
    FULL_PROFILE,
    LOCAL_PROFILE,
    profile_examples,
)

# Hypothesis's own default, the count of a test that declares none.
HYPOTHESIS_DEFAULT_EXAMPLES = 100
# The cap the `local-profile-count` Assertion states.
LOCAL_CAP = 10
# Declared counts on both sides of the local cap, and the cap itself.
DECLARED_COUNTS = (1, 5, LOCAL_CAP - 1, LOCAL_CAP, LOCAL_CAP + 1, 40, 200)
SETTING_NAMES = tuple(
    name for name in inspect.signature(settings).parameters if name != "parent"
)


def test_a_run_that_names_no_profile_loads_full() -> None:
    run = loaded_profile()

    assert run.exit_code == 0, run.output
    assert run.profile == FULL_PROFILE
    assert run.example_count == HYPOTHESIS_DEFAULT_EXAMPLES


@pytest.mark.parametrize(
    ("profile", "example_count"),
    ((FULL_PROFILE, HYPOTHESIS_DEFAULT_EXAMPLES), (LOCAL_PROFILE, LOCAL_CAP)),
)
def test_a_run_that_names_a_profile_loads_it(profile: str, example_count: int) -> None:
    run = loaded_profile(f"--hypothesis-profile={profile}")

    assert run.exit_code == 0, run.output
    assert run.profile == profile
    assert run.example_count == example_count


def test_the_full_profile_runs_every_declared_count() -> None:
    with profile_loaded(FULL_PROFILE):
        assert [profile_examples(count) for count in DECLARED_COUNTS] == list(
            DECLARED_COUNTS
        )
        assert settings.default.max_examples == HYPOTHESIS_DEFAULT_EXAMPLES
    assert FULL_MAX_EXAMPLES == HYPOTHESIS_DEFAULT_EXAMPLES


def test_the_local_profile_runs_the_declared_count_or_ten() -> None:
    with profile_loaded(LOCAL_PROFILE):
        assert [profile_examples(count) for count in DECLARED_COUNTS] == [
            min(count, LOCAL_CAP) for count in DECLARED_COUNTS
        ]
        assert settings.default.max_examples == LOCAL_CAP


def test_the_local_profile_keeps_every_other_full_setting() -> None:
    full = settings.get_profile(FULL_PROFILE)
    local = settings.get_profile(LOCAL_PROFILE)
    others = tuple(name for name in SETTING_NAMES if name != "max_examples")

    assert others
    assert {name: getattr(local, name) for name in others} == {
        name: getattr(full, name) for name in others
    }


def test_every_declared_count_reads_the_loaded_profile() -> None:
    assert unrouted_example_counts() == ()

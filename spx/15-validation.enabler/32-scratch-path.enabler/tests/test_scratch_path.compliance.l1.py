import pytest

from outcomeeng.validation.scratch_paths import find_fixed_temporary_paths
from outcomeeng_testing.generators.scratch_paths import (
    fixed_temporary_paths,
    portable_scratch_sources,
)
from outcomeeng_testing.harnesses.scratch_paths import observe_allow_marker_lines

MARKED_LINE = 1
UNMARKED_LINE = 2


@pytest.mark.parametrize("reference", fixed_temporary_paths())
def test_fixed_temporary_category_is_flagged(reference: str) -> None:
    assert find_fixed_temporary_paths(reference), (
        f"prohibited category passed unflagged: {reference!r}"
    )


@pytest.mark.parametrize("reference", portable_scratch_sources())
def test_portable_scratch_category_is_accepted(reference: str) -> None:
    found = find_fixed_temporary_paths(reference)
    assert not found, f"portable category flagged: {reference!r} -> {found!r}"


def test_allow_marker_exempts_only_its_own_line() -> None:
    reported = observe_allow_marker_lines()

    assert MARKED_LINE not in reported, (
        f"marked line {MARKED_LINE} was reported: {reported!r}"
    )
    assert UNMARKED_LINE in reported, (
        f"unmarked line {UNMARKED_LINE} was not reported: {reported!r}"
    )

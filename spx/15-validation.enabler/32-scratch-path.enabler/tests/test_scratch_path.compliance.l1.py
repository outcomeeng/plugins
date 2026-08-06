import pytest

from outcomeeng.validation.scratch_paths import find_fixed_temporary_paths
from outcomeeng_testing.generators.scratch_paths import (
    fixed_temporary_paths,
    portable_scratch_sources,
)
from outcomeeng_testing.harnesses.scratch_paths import observe_allow_marker_lines


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
    observed = observe_allow_marker_lines()

    assert observed.marked_line not in observed.reported_lines, (
        f"marked line {observed.marked_line} was reported: {observed.reported_lines!r}"
    )
    assert observed.unmarked_line in observed.reported_lines, (
        f"unmarked line {observed.unmarked_line} was not reported: "
        f"{observed.reported_lines!r}"
    )

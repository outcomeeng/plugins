from outcomeeng_testing.harnesses.scratch_paths import (
    allow_marker_exempts_only_its_own_line,
    every_fixed_temporary_category_is_flagged,
    every_portable_scratch_category_is_accepted,
)


def test_allow_marker_exempts_only_its_own_line() -> None:
    assert allow_marker_exempts_only_its_own_line()


def test_every_fixed_temporary_category_is_flagged() -> None:
    assert every_fixed_temporary_category_is_flagged()


def test_every_portable_scratch_category_is_accepted() -> None:
    assert every_portable_scratch_category_is_accepted()

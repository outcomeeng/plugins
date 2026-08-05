from outcomeeng_testing.harnesses.scratch_paths import (
    every_fixed_temporary_category_is_flagged,
    every_portable_scratch_category_is_accepted,
)


def test_every_fixed_temporary_category_is_flagged() -> None:
    assert every_fixed_temporary_category_is_flagged()


def test_every_portable_scratch_category_is_accepted() -> None:
    assert every_portable_scratch_category_is_accepted()

from outcomeeng_testing.harnesses.reference_portability import (
    every_nonportable_category_is_flagged,
    every_portable_category_is_accepted,
)


def test_every_nonportable_category_is_flagged() -> None:
    assert every_nonportable_category_is_flagged()


def test_every_portable_category_is_accepted() -> None:
    assert every_portable_category_is_accepted()

from outcomeeng_testing.harnesses.contribution_targeting import (
    verify_permission_never_inferred,
)


def test_permission_never_inferred() -> None:
    assert verify_permission_never_inferred() == []

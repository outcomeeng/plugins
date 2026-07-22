from outcomeeng_testing.harnesses.prowl_environment import verify_prowl_compliance


def test_prowl_environment_compliance() -> None:
    assert verify_prowl_compliance() == []

from outcomeeng_testing.harnesses.prowl_environment import verify_prowl_properties


def test_prowl_environment_properties() -> None:
    assert verify_prowl_properties() == []

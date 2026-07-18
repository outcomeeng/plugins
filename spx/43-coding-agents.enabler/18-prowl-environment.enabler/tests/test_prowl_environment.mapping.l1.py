from outcomeeng_testing.harnesses.prowl_environment import verify_prowl_mappings


def test_prowl_environment_mappings() -> None:
    assert verify_prowl_mappings() == []

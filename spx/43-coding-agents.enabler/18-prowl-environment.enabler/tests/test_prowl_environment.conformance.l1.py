from outcomeeng_testing.harnesses.prowl_environment import verify_prowl_conformance


def test_prowl_environment_conformance() -> None:
    assert verify_prowl_conformance() == []

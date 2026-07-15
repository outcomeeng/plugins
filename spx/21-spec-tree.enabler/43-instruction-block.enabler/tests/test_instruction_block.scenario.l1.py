from outcomeeng_testing.harnesses import instruction_block as harness


def test_instruction_block_scenario_evidence() -> None:
    assert harness.scenario_evidence_is_valid()

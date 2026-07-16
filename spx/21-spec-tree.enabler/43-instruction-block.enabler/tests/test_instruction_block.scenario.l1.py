from outcomeeng_testing.harnesses import instruction_block_scenario_evidence as evidence


def test_instruction_block_scenario_evidence() -> None:
    assert (
        evidence.scenario_evidence_run().executed
        == evidence.scenario_evidence_declarations()
    )

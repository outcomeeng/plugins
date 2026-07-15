from outcomeeng_testing.harnesses import instruction_block_scenario_evidence as evidence


def test_instruction_block_scenario_evidence() -> None:
    run = evidence.scenario_evidence_run()
    assert run.executed == run.declared

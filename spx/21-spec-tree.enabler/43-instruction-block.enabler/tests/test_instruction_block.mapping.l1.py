from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_mapping_evidence as evidence

MODULE = harness.load_instruction_block_module()


def test_instruction_block_mapping_evidence() -> None:
    assert (
        evidence.mapping_evidence_run().executed
        == evidence.mapping_evidence_declarations()
    )


def test_root_body_shape_maps_to_delegation_verdict() -> None:
    other = harness.INSTRUCTION_AGENTS
    verdicts = {
        case.name: MODULE.delegates_to(case.body, other)
        for case in harness.delegation_shape_cases()
    }
    assert verdicts == {
        "every-substantive-line-references": True,
        "a-substantive-line-does-not-reference": False,
        "no-substantive-line": False,
        "reference-inside-a-code-fence": False,
    }

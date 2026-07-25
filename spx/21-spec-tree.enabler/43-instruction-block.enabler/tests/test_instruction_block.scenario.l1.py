import pathlib

from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_scenario_evidence as evidence

MODULE = harness.load_instruction_block_module()


def test_instruction_block_scenario_evidence() -> None:
    assert (
        evidence.scenario_evidence_run().executed
        == evidence.scenario_evidence_declarations()
    )


def test_delegating_root_file_adopts_the_content_bearing_body(
    tmp_path: pathlib.Path,
) -> None:
    outcome = harness.observe_bootstrap_outcome(
        tmp_path, harness.root_instruction_topology_delegating
    )
    pointer = outcome.seeds[harness.INSTRUCTION_CLAUDE].strip()
    shared_body = harness.ROOT_AGENTS_BODY.strip("\n")

    assert MODULE.parse_shared_regions(outcome.claude) == {
        harness.SHARED_REGION_NAME: shared_body
    }
    assert MODULE.parse_shared_regions(outcome.agents) == {
        harness.SHARED_REGION_NAME: shared_body
    }
    assert pointer not in outcome.claude
    assert pointer not in outcome.agents
    assert outcome.claude.startswith(MODULE.ROUTER_MARKER_PREFIX)
    assert outcome.agents.startswith(MODULE.ROUTER_MARKER_PREFIX)


def test_mutually_delegating_root_files_adopt_neither_body(
    tmp_path: pathlib.Path,
) -> None:
    outcome = harness.observe_bootstrap_outcome(
        tmp_path, harness.root_instruction_topology_mutual_delegation
    )

    assert MODULE.parse_shared_regions(outcome.claude) == {}
    assert MODULE.parse_shared_regions(outcome.agents) == {}
    assert outcome.seeds[harness.INSTRUCTION_CLAUDE].strip() in outcome.claude
    assert outcome.seeds[harness.INSTRUCTION_AGENTS].strip() in outcome.agents
    assert outcome.claude.startswith(MODULE.ROUTER_MARKER_PREFIX)
    assert outcome.agents.startswith(MODULE.ROUTER_MARKER_PREFIX)

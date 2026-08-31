"""Scenario evidence for root instruction-file topology materialization."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_symlinked_harness_instruction_files_materialize_as_regular_files() -> None:
    observation = harness.observe_symlinked_instruction_topology_materialization()

    assert observation.claude_is_file
    assert observation.agents_is_file
    assert not observation.claude_is_symlink
    assert not observation.agents_is_symlink
    assert observation.claude_body == harness.ROOT_SHARED_BODY
    assert observation.agents_body == harness.ROOT_SHARED_BODY
    assert observation.claude_seed == harness.ROOT_SHARED_BODY
    assert observation.agents_seed == harness.ROOT_SHARED_BODY

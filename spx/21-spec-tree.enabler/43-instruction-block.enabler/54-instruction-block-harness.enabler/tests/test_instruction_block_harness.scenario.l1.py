"""Scenario evidence for root instruction-file topology materialization."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_symlinked_harness_instruction_files_materialize_as_regular_files() -> None:
    assert harness.symlinked_instruction_topology_materializes_as_regular_files()

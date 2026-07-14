"""Scenario evidence for root instruction-file topology materialization."""

from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_oracle as oracle


def test_claude_symlink_materializes_as_regular_instruction_files() -> None:
    assert (
        harness.observe_claude_symlink_materialization()
        == oracle.claude_symlink_materialization()
    )


def test_agents_symlink_materializes_as_regular_instruction_files() -> None:
    assert (
        harness.observe_agents_symlink_materialization()
        == oracle.agents_symlink_materialization()
    )

"""Scenario evidence for root instruction-file topology materialization."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_claude_symlink_materializes_as_regular_instruction_files() -> None:
    assert (
        harness.observe_claude_symlink_materialization().actual
        == harness.observe_claude_symlink_materialization().expected
    )


def test_agents_symlink_materializes_as_regular_instruction_files() -> None:
    assert (
        harness.observe_agents_symlink_materialization().actual
        == harness.observe_agents_symlink_materialization().expected
    )

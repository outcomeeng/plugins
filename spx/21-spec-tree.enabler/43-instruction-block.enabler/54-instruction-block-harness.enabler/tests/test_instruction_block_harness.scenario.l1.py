"""Scenario evidence for root instruction-file topology materialization."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_symlinked_harness_instruction_files_materialize_as_regular_files() -> None:
    for topology in (
        harness.root_instruction_topology_claude_symlink(),
        harness.root_instruction_topology_agents_symlink(),
    ):
        body = next(iter(topology.files.values()))
        with harness.temporary_instruction_root() as root:
            materialized = harness.materialize_root_instruction_topology(root, topology)
            claude_path = root / harness.INSTRUCTION_CLAUDE
            agents_path = root / harness.INSTRUCTION_AGENTS

            assert claude_path.is_file()
            assert agents_path.is_file()
            assert not claude_path.is_symlink()
            assert not agents_path.is_symlink()
            assert claude_path.read_text(encoding="utf-8") == body
            assert agents_path.read_text(encoding="utf-8") == body
            assert materialized[harness.INSTRUCTION_CLAUDE] == body
            assert materialized[harness.INSTRUCTION_AGENTS] == body

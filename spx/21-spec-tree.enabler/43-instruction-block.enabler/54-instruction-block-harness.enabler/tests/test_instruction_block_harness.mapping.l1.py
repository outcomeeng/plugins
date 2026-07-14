"""Mapping evidence for instruction-block harness contracts."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_only_claude_topology_maps_to_both_harnesses() -> None:
    topology = harness.root_instruction_topology_only_claude()
    body = topology.files[harness.INSTRUCTION_CLAUDE]
    with harness.temporary_instruction_root() as root:
        assert harness.materialize_root_instruction_topology(root, topology) == {
            harness.INSTRUCTION_CLAUDE: body,
            harness.INSTRUCTION_AGENTS: body,
        }


def test_only_agents_topology_maps_to_both_harnesses() -> None:
    topology = harness.root_instruction_topology_only_agents()
    body = topology.files[harness.INSTRUCTION_AGENTS]
    with harness.temporary_instruction_root() as root:
        assert harness.materialize_root_instruction_topology(root, topology) == {
            harness.INSTRUCTION_CLAUDE: body,
            harness.INSTRUCTION_AGENTS: body,
        }


def test_separate_topology_maps_each_harness_body() -> None:
    topology = harness.root_instruction_topology_separate()
    with harness.temporary_instruction_root() as root:
        assert (
            harness.materialize_root_instruction_topology(root, topology)
            == topology.files
        )


def test_symlinked_topology_maps_shared_body() -> None:
    for topology in (
        harness.root_instruction_topology_claude_symlink(),
        harness.root_instruction_topology_agents_symlink(),
    ):
        body = next(iter(topology.files.values()))
        with harness.temporary_instruction_root() as root:
            assert harness.materialize_root_instruction_topology(root, topology) == {
                harness.INSTRUCTION_CLAUDE: body,
                harness.INSTRUCTION_AGENTS: body,
            }

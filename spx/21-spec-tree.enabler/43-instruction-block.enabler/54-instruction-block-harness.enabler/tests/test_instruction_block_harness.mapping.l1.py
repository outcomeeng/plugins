"""Mapping evidence for instruction-block harness contracts."""

from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import instruction_block_oracle as oracle


def test_only_claude_topology_maps_to_both_harnesses() -> None:
    assert (
        harness.observe_only_claude_topology_mapping()
        == oracle.only_claude_topology_mapping()
    )


def test_only_agents_topology_maps_to_both_harnesses() -> None:
    assert (
        harness.observe_only_agents_topology_mapping()
        == oracle.only_agents_topology_mapping()
    )


def test_separate_topology_maps_each_harness_body() -> None:
    assert (
        harness.observe_separate_topology_mapping()
        == oracle.separate_topology_mapping()
    )


def test_claude_symlinked_topology_maps_shared_body() -> None:
    assert (
        harness.observe_claude_symlink_topology_mapping()
        == oracle.claude_symlink_topology_mapping()
    )


def test_agents_symlinked_topology_maps_shared_body() -> None:
    assert (
        harness.observe_agents_symlink_topology_mapping()
        == oracle.agents_symlink_topology_mapping()
    )

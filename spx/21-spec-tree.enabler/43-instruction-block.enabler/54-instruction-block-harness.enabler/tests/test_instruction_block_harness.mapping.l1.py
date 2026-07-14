"""Mapping evidence for instruction-block harness contracts."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_only_claude_topology_maps_to_both_harnesses() -> None:
    assert (
        harness.observe_only_claude_topology_mapping().actual
        == harness.observe_only_claude_topology_mapping().expected
    )


def test_only_agents_topology_maps_to_both_harnesses() -> None:
    assert (
        harness.observe_only_agents_topology_mapping().actual
        == harness.observe_only_agents_topology_mapping().expected
    )


def test_separate_topology_maps_each_harness_body() -> None:
    assert (
        harness.observe_separate_topology_mapping().actual
        == harness.observe_separate_topology_mapping().expected
    )


def test_claude_symlinked_topology_maps_shared_body() -> None:
    assert (
        harness.observe_claude_symlink_topology_mapping().actual
        == harness.observe_claude_symlink_topology_mapping().expected
    )


def test_agents_symlinked_topology_maps_shared_body() -> None:
    assert (
        harness.observe_agents_symlink_topology_mapping().actual
        == harness.observe_agents_symlink_topology_mapping().expected
    )

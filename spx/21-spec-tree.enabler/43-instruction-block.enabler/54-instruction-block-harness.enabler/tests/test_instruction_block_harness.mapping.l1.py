"""Mapping evidence for instruction-block harness contracts."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_only_claude_topology_maps_to_both_harnesses() -> None:
    harness.assert_only_claude_topology_maps_to_both_harnesses()


def test_only_agents_topology_maps_to_both_harnesses() -> None:
    harness.assert_only_agents_topology_maps_to_both_harnesses()


def test_separate_topology_maps_each_harness_body() -> None:
    harness.assert_separate_topology_maps_each_harness_body()


def test_symlinked_topology_maps_shared_body() -> None:
    harness.assert_symlinked_topology_maps_shared_body()


def test_canonical_template_maps_configured_agent_identity_protocol() -> None:
    harness.assert_canonical_configured_agent_identity_protocol()

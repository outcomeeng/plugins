"""Mapping evidence for configured-agent identity verification in Codex."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_codex_render_maps_agent_launch_to_identity_preflight() -> None:
    harness.assert_canonical_configured_agent_identity_protocol()

"""Mapping evidence for configured-agent identity verification in Codex."""

import json
import re

from outcomeeng.distribution.agents import CODEX_AGENT_ENV_VAR
from outcomeeng_testing.harnesses import instruction_block as harness


def test_codex_render_maps_agent_launch_to_identity_preflight() -> None:
    template = harness.read_canonical_template()
    module = harness.load_instruction_block_module()
    version = module.parse_template_version(template)
    codex = module.render(
        template,
        harness.TEMPLATE_LANGUAGES,
        version,
        harness.HARNESS_CODEX,
    )
    claude = module.render(
        template,
        harness.TEMPLATE_LANGUAGES,
        version,
        harness.HARNESS_CLAUDE,
    )
    protocol_steps = tuple(
        json.loads(body)
        for body in re.findall(r"```json\n(.*?)\n```", codex, re.DOTALL)
    )
    spawn_step, role_step = protocol_steps[:2]

    assert CODEX_AGENT_ENV_VAR in codex
    assert CODEX_AGENT_ENV_VAR in spawn_step["arguments"]["message"]
    assert "agent_type" in spawn_step["arguments"]
    assert role_step["arguments"]["target"] == (
        f"<agent-id-from-{spawn_step['tool'].rsplit('.', maxsplit=1)[-1].replace('_', '-')}>"
    )
    assert "agent_type" not in role_step["arguments"]
    assert role_step["tool"] != spawn_step["tool"]
    assert CODEX_AGENT_ENV_VAR not in claude

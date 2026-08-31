"""Rendered instruction-block observations for linked compliance evidence."""

from __future__ import annotations

from typing import cast

from outcomeeng.distribution import instruction_block as dist
from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


def _distribution_module() -> dist.InstructionBlockModule:
    """Narrow the dynamic script module at distribution-helper boundaries."""
    return cast(dist.InstructionBlockModule, MODULE)


def rendered_instruction_blocks(
    enabled_languages: tuple[str, ...] = harness.TEMPLATE_LANGUAGES,
) -> dict[str, str]:
    """Render shipped harness templates without judging the rendered content."""
    templates = dist.load_harness_templates(_distribution_module())
    return dist.render_instruction_blocks_from_harness_templates(
        _distribution_module(), templates, enabled_languages
    )

"""Compliance evidence: shipped plugin content carries no non-portable reference.

Spec: spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md

Rule: NEVER a committed file under ``src/plugins/`` references a concrete path into this
marketplace's own files — a numbered ``spx/`` node or decision, or a ``src/``/``dist/``/
``outcomeeng/`` repository segment. The detection rule lives in the source module under
test; this test imports it and exercises a violating case per forbidden category against a
portable case per allowed category, so enforcement is neither trivially always-failing nor
blind to our own references.
"""

from __future__ import annotations

import pytest

from outcomeeng.validation.reference_portability import find_nonportable

# One reference per forbidden category — each must be flagged.
NONPORTABLE_SAMPLES = [
    "spx/13-plugin-and-runtime-conventions.adr.md",  # numbered product decision
    "spx/15-validation.enabler/65-gate.enabler",  # numbered product node
    "src/plugins/spec-tree/skills/applying/SKILL.md",  # authored-source path
    "src/cli/index.ts",  # repository source path outside src/plugins
    "dist/claude/spec-tree/agents/applier.md",  # generated-runtime path
    "outcomeeng/validation/_steps.py",  # toolchain package path
    "/home/dev/checkout/dist/claude/spec-tree/agents/applier.md",  # absolute checkout path
]

# One reference per allowed category — none may be flagged.
PORTABLE_SAMPLES = [
    "spx/{node-path}/{slug}.md",  # generic consumer-tree placeholder
    "spx/<full-path>",  # generic consumer-tree placeholder
    "spx/EXCLUDE",  # methodology-universal file
    "spx/CLAUDE.md",  # methodology-universal file
    "spx/local/python.md",  # methodology-universal directory
    "spx/sessions/todo/",  # methodology-universal directory
    "spx/1foo",  # 'spx/' + digit without the 'NN-' node prefix is not a node reference
    ".dist/claude/build-artifact.md",  # dot-prefixed build dir, not the marketplace dist/
    "${CLAUDE_SKILL_DIR}/references/x.md",  # the plugin's own files
    "${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json",  # the plugin's own files
]


@pytest.mark.parametrize("reference", NONPORTABLE_SAMPLES)
def test_nonportable_reference_is_flagged(reference: str) -> None:
    found = find_nonportable(f"see {reference} for details")
    assert found, f"{reference!r} must be flagged as non-portable"


@pytest.mark.parametrize("reference", PORTABLE_SAMPLES)
def test_portable_reference_is_not_flagged(reference: str) -> None:
    assert find_nonportable(f"see {reference} for details") == []

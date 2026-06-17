"""Compliance evidence: shipped plugin content carries no non-portable reference.

Spec: spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md

Rule: NEVER a committed file under ``src/plugins/`` references a concrete path into this
marketplace's own files — a numbered ``spx/\\d+-`` node or decision, or a path under a
marketplace root (``src/plugins/``, ``dist/claude/``, ``dist/codex/``, an ``outcomeeng``
toolchain package, or the marketplace's own repo slug as in ``outcomeeng/plugins/AGENTS.md``).
The validator passes universal conventions a consumer checkout also resolves — the
``55-example`` illustrative root sentinel, a bare ``src/``/``dist/`` path, and the
marketplace's own bare GitHub org/repo slug. The detection rule lives in the source module under
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
    "src/plugins/spec-tree/skills/apply/SKILL.md",  # authored-source root
    "dist/claude/spec-tree/agents/applier.md",  # generated Claude runtime root
    "dist/codex/spec-tree/agents/applier.md",  # generated Codex runtime root
    "outcomeeng/validation/_steps.py",  # toolchain package path
    "outcomeeng_testing/harnesses/spec_tree.py",  # toolchain test-package path
    "outcomeeng/plugins/AGENTS.md",  # path under the marketplace's own repo slug
    "outcomeeng/spx/src/types.ts",  # path under a sibling repo slug, not the bare slug
    "/home/dev/checkout/dist/claude/spec-tree/agents/applier.md",  # absolute checkout path
    "spx/NN-infra.enabler/NN-parser.outcome",  # invalid index-placeholder path
]

# One reference per allowed category — none may be flagged.
PORTABLE_SAMPLES = [
    "spx/{node-path}/{slug}.md",  # generic consumer-tree placeholder
    "spx/<full-path>",  # generic consumer-tree placeholder
    "spx/55-example.enabler",  # illustrative root sentinel
    "spx/55-example.enabler/12-parser.outcome",  # illustrative root sentinel
    "spx/55-example.outcome/43-integration.outcome",  # illustrative root sentinel with outcome type
    "spx/EXCLUDE",  # methodology-universal file
    "spx/CLAUDE.md",  # methodology-universal file
    "spx/local/python.md",  # methodology-universal directory
    "spx/sessions/todo/",  # methodology-universal directory
    "spx/1foo",  # 'spx/' + digit without the 'NN-' node prefix is not a node reference
    "src/index.ts",  # universal source-tree convention, not a marketplace root
    "src/orders/processor.ts",  # generic example source path every consumer can hold
    "dist/output.js",  # bare build dir, not the marketplace dist/claude or dist/codex
    ".dist/claude/build-artifact.md",  # dot-prefixed build dir, not the marketplace dist/
    "outcomeeng/plugins",  # the marketplace's own bare GitHub org/repo slug (no trailing path)
    "outcomeeng/spx",  # the marketplace's own bare GitHub org/repo slug (no trailing path)
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

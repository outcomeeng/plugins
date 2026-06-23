"""Path access for the ``32-session-skill-invocation.enabler`` tests.

The compliance test under
``spx/21-spec-tree.enabler/76-sessions.enabler/32-session-skill-invocation.enabler/tests/``
verifies that no slash-command shim exposes the ``/handoff`` or ``/pickup``
session workflows. That check is a filesystem invariant over the spec-tree
commands directory, so the harness exposes only the directory path per
``spx/15-test-infrastructure.pdr.md`` — shared test scaffolding is production
code outside ``tests/`` and outside ``spx/``.

The node's other declared-surface assertions carry ``[audit]`` evidence: parsing
the authored ``SKILL.md`` frontmatter or workflow prose to assert the declared
surface is the wrong layer for a ``[test]`` (``spx/15-spec-coverage.adr.md``,
``spx/12-shipped-scripting.adr.md``), so this harness carries no artifact reader.
"""

from __future__ import annotations

from pathlib import Path

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/session_skill_invocation.py`` (harnesses ->
# outcomeeng_testing -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]

COMMANDS_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "commands"

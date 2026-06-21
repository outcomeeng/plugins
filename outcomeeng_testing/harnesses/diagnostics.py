"""Harness for the diagnostics node tests.

The diagnostics node's conformance test reads the shipped ``diagnose`` skill
from the committed ``dist/`` tree to verify the build rendered the spx version
floor into it. The repository-root constant and the dist reader live here
because shared test scaffolding is production code outside ``tests/`` and
outside ``spx/``.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.dist_tree import DistTreeReader

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/diagnostics.py`` (harnesses ->
# outcomeeng_testing -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]

# The plugin and skill the diagnostics node ships.
SPEC_TREE_PLUGIN = "spec-tree"
DIAGNOSE_SKILL = "diagnose"

# The authored ``diagnose`` skill the build renders into ``dist/``.
AUTHORED_DIAGNOSE_SKILL = (
    REPO_ROOT
    / "src"
    / "plugins"
    / SPEC_TREE_PLUGIN
    / "skills"
    / DIAGNOSE_SKILL
    / "SKILL.md"
)

# The build template token the authored skill uses to source the spx version
# floor; the build's render pass replaces it with the source-of-truth value.
SPX_FLOOR_TOKEN = "{{! spx_floor !}}"


def authored_diagnose_text() -> str:
    """Return the authored ``diagnose`` skill body."""
    return AUTHORED_DIAGNOSE_SKILL.read_text(encoding="utf-8")


def shipped_dist_reader() -> DistTreeReader:
    """Return a reader over the committed ``dist/`` tree at the repository root."""
    return DistTreeReader(REPO_ROOT)

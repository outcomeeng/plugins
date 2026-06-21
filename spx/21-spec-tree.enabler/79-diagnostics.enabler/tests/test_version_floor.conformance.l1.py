"""Conformance evidence for the shipped diagnose skill's spx version floor.

The diagnostics node declares that the version floor the shipped diagnose skill
carries equals the product's single source-of-truth spx-version floor, on every
shipped target. The authored skill sources the floor through the build's
template token; the build renders that token into the source-of-truth value for
each target. These tests verify both halves of that contract against the real
authored source and the committed dist tree.
"""

from __future__ import annotations

from outcomeeng.distribution.contracts import Target
from outcomeeng.validation.spx_version import REQUIRED_SPX_VERSION
from outcomeeng_testing.harnesses.diagnostics import (
    DIAGNOSE_SKILL,
    SPEC_TREE_PLUGIN,
    SPX_FLOOR_TOKEN,
    authored_diagnose_text,
    shipped_dist_reader,
)


def test_authored_skill_sources_the_floor_through_the_build_token() -> None:
    """The authored skill carries the floor token, not a hand-written value."""
    assert SPX_FLOOR_TOKEN in authored_diagnose_text()


def test_each_shipped_target_renders_the_source_of_truth_floor() -> None:
    """Every shipped target carries the rendered floor and no raw token."""
    reader = shipped_dist_reader()
    for target in Target:
        body = reader.read_skill_body(SPEC_TREE_PLUGIN, DIAGNOSE_SKILL, target=target)
        assert REQUIRED_SPX_VERSION in body
        assert SPX_FLOOR_TOKEN not in body

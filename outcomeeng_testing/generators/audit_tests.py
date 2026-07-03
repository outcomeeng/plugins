"""Generators for audit-tests evidence."""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.test_evidence import COUPLING_TAXONOMY_CATEGORIES, CouplingEvidence


def coupling_taxonomy_categories() -> SearchStrategy[CouplingEvidence]:
    return st.sampled_from(sorted(COUPLING_TAXONOMY_CATEGORIES, key=str))

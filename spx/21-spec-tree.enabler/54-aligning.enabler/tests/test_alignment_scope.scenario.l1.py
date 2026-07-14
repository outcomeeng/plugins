"""Scenario evidence for alignment changeset-scope derivation."""

from outcomeeng_testing.harnesses.alignment_scope import (
    assert_alignment_reports_unconfigured_base,
    assert_alignment_uses_canonical_changeset_scope,
)


def test_alignment_uses_canonical_changeset_scope() -> None:
    assert_alignment_uses_canonical_changeset_scope()


def test_alignment_reports_unconfigured_base() -> None:
    assert_alignment_reports_unconfigured_base()

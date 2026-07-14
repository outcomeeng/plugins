"""Property evidence for directive parse/format inversion."""

from __future__ import annotations

from outcomeeng_testing.harnesses.source_and_templating import (
    directive_roundtrip_property_holds,
    property_failure_notes_include_seed_and_replay,
)


def test_parse_of_format_yields_original_directive() -> None:
    assert directive_roundtrip_property_holds()


def test_property_failures_report_seed_and_replay_path() -> None:
    assert property_failure_notes_include_seed_and_replay()

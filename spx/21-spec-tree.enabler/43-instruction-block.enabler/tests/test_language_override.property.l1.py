"""Property evidence for explicit language override validation."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_unsupported_language_overrides_are_rejected() -> None:
    assert (
        harness.unsupported_language_override_evidence_run().executed
        == harness.unsupported_language_override_declarations()
    )

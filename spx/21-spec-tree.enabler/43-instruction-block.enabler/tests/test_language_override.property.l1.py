"""Property evidence for explicit language override validation."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_unsupported_language_overrides_are_rejected() -> None:
    def assert_rejected(observation: harness.LanguageOverrideObservation) -> None:
        assert observation.returncode != 0
        assert observation.token in observation.stderr
        assert all(
            language in observation.stderr
            for language in observation.supported_languages
        )

    harness.for_all_unsupported_language_overrides(assert_rejected)

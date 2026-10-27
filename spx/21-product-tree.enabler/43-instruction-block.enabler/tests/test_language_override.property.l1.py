"""Property evidence for explicit language override validation."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_unsupported_language_overrides_are_rejected() -> None:
    def rejects_the_token(observation: harness.LanguageOverrideObservation) -> None:
        assert observation.returncode != 0, observation.token
        assert observation.token in observation.stderr
        for language in observation.supported_languages:
            assert language in observation.stderr, language

    harness.for_all_unsupported_language_overrides(rejects_the_token)

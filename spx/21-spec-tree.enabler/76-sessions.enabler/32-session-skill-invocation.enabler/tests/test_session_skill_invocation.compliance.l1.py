"""Compliance tests for 32-session-skill-invocation.enabler.

Verify that the `/handoff` and `/pickup` session workflows are reachable only
through their skills — no slash-command shim exposes them. This is a filesystem
invariant the test can establish without parsing any authored artifact.

The other declared-surface assertions in this node — argument-hint flags, the
injected `spx session` queue, and `/pickup` workflow ordering — carry `[audit]`
evidence rather than `[test]`. Asserting them by parsing the authored SKILL.md
frontmatter or workflow prose in this harness is the wrong layer for a `[test]`
per spx/15-spec-coverage.adr.md and spx/12-shipped-scripting.adr.md; an auditor
reads the declared surface directly.
"""

from outcomeeng_testing.harnesses.session_skill_invocation import COMMANDS_DIR


class TestNoSlashCommandShims:
    def test_no_handoff_command_shim(self) -> None:
        assert not (COMMANDS_DIR / "handoff.md").exists()

    def test_no_pickup_command_shim(self) -> None:
        assert not (COMMANDS_DIR / "pickup.md").exists()

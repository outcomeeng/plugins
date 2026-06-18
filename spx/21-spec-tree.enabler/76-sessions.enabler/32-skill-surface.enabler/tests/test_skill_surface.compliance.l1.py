"""Compliance tests for 32-skill-surface.enabler.

Verify the declared invocation surface of the `/handoff` and `/pickup` session
skills: their argument-hint flags, the live `spx session` queue injected into
each context block, and the absence of slash-command shims for the session
workflows. All read the real authored skill artifacts — no doubles.
"""

from outcomeeng_testing.harnesses.skill_surface import (
    COMMANDS_DIR,
    HANDOFF_SKILL,
    PICKUP_SKILL,
    PICKUP_WORKFLOW,
    argument_hint,
    context_block,
    file_text,
)


class TestArgumentHints:
    def test_handoff_declares_argument_hint(self) -> None:
        assert argument_hint(HANDOFF_SKILL) == "[--no-session] [--prune]"

    def test_pickup_declares_argument_hint(self) -> None:
        assert argument_hint(PICKUP_SKILL) == "[--list] [--auto-continue]"


class TestContextInjection:
    def test_handoff_injects_session_list(self) -> None:
        assert "spx session list" in context_block(HANDOFF_SKILL)

    def test_pickup_injects_session_todo(self) -> None:
        assert "spx session todo" in context_block(PICKUP_SKILL)


class TestPickupWorkflowOrdering:
    def test_pickup_loads_foundation_before_session_details(self) -> None:
        workflow = file_text(PICKUP_WORKFLOW)

        understand_index = workflow.index(
            'Skill tool -> { "skill": "spec-tree:understand" }'
        )
        skills_checklist_index = workflow.index("**Step 3: Present skills checklist**")

        assert understand_index < skills_checklist_index

    def test_pickup_defers_coordination_note_reads_to_contextualize(self) -> None:
        workflow = file_text(PICKUP_WORKFLOW)

        no_read_index = workflow.index(
            "Do not read `PLAN.md` or `ISSUES.md` content in this step"
        )
        contextualize_index = workflow.index('{ "skill": "spec-tree:contextualize"')
        context_reads_index = workflow.index("`/contextualize` reads the note content")

        assert no_read_index < contextualize_index < context_reads_index


class TestNoSlashCommandShims:
    def test_no_handoff_command_shim(self) -> None:
        assert not (COMMANDS_DIR / "handoff.md").exists()

    def test_no_pickup_command_shim(self) -> None:
        assert not (COMMANDS_DIR / "pickup.md").exists()

"""Bounded case domains for review-changes finding-citation evidence."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class RejectedRuleCitationCase:
    """One violating ``Finding.rule`` value named by the rule class it breaks."""

    violation_class: str
    rule: str


def rejected_rule_citation_cases() -> Iterator[RejectedRuleCitationCase]:
    """Yield one violating value per rejected class the citation rule names.

    The governing assertion states that ``Finding.rule`` is never a free-form
    description, a required-action string, a repository-root review policy
    citation, or a tracking-location string, that a relative ``SKILL.md`` slug
    citation is not uniquely resolvable, and that every citation must resolve to
    an existing file and rule. Each case follows one of those stated classes.
    """
    yield RejectedRuleCitationCase("empty", "")
    yield RejectedRuleCitationCase("free-form-description", "fix the typo")
    yield RejectedRuleCitationCase(
        "required-action-string", "rename the symbol to convey its role"
    )
    yield RejectedRuleCitationCase(
        "repository-root-review-policy", "REVIEW.md:not-a-real-rule-slug"
    )
    yield RejectedRuleCitationCase("tracking-location", "Track under: ISSUES.md")
    yield RejectedRuleCitationCase(
        "relative-skill-citation", "SKILL.md:render-templates-as-data"
    )
    yield RejectedRuleCitationCase(
        "spec-assertion-without-index",
        "spx/21-spec-tree.enabler/68-reviewing.enabler/"
        "21-reviewing-changes.enabler/reviewing-changes.md:SCENARIO",
    )
    yield RejectedRuleCitationCase(
        "spec-assertion-nonexistent-file", "spx/does-not-exist.md:ALWAYS:1"
    )
    yield RejectedRuleCitationCase(
        "decision-nonexistent-file",
        "spx/21-spec-tree.enabler/68-reviewing.enabler/"
        "21-reviewing-changes.enabler/99-nonexistent.adr.md",
    )
    yield RejectedRuleCitationCase(
        "spec-assertion-beyond-declared-count",
        "spx/21-spec-tree.enabler/68-reviewing.enabler/"
        "21-reviewing-changes.enabler/reviewing-changes.md:SCENARIO:999",
    )
    yield RejectedRuleCitationCase("wrong-tree-prefix", "spec/auth.md:ALWAYS:1")
    yield RejectedRuleCitationCase(
        "plugin-skill-without-slug", "plugins/spec-tree/skills/review-changes/SKILL.md"
    )
    yield RejectedRuleCitationCase(
        "plugin-skill-unknown-slug",
        "plugins/spec-tree/skills/review-changes/SKILL.md:not-a-real-rule-slug",
    )
    yield RejectedRuleCitationCase("root-rule-without-slug", "AGENTS.md")
    yield RejectedRuleCitationCase(
        "root-rule-unknown-slug", "AGENTS.md:not-a-real-rule-slug"
    )

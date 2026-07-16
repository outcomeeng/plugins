"""Generated domains for review-changes evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hypothesis import strategies as st

from outcomeeng_testing.harnesses.reviewing_changes import (
    load_review_result_module,
    make_finding_dict,
)


@dataclass(frozen=True)
class RuleCitationCase:
    """One independent citation oracle paired with its source family."""

    family: Any
    citation: str


def valid_rule_citation_cases() -> tuple[RuleCitationCase, ...]:
    """Return one fixed independent citation for every source-owned family."""

    review_result = load_review_result_module()
    return (
        RuleCitationCase(
            review_result.RuleCitationFamily.SPEC_ASSERTION,
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:ALWAYS:1",
        ),
        RuleCitationCase(
            review_result.RuleCitationFamily.DECISION,
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md",
        ),
        RuleCitationCase(
            review_result.RuleCitationFamily.DECISION,
            "spx/15-agent-tools.pdr.md",
        ),
        RuleCitationCase(
            review_result.RuleCitationFamily.PLUGIN_SKILL,
            "plugins/spec-tree/skills/review-changes/SKILL.md:objective",
        ),
        RuleCitationCase(
            review_result.RuleCitationFamily.ROOT_GUIDE,
            "AGENTS.md:spec-tree-instructions",
        ),
        RuleCitationCase(
            review_result.RuleCitationFamily.ROOT_GUIDE,
            "CLAUDE.md:spec-tree-instructions",
        ),
    )


def review_findings() -> st.SearchStrategy[Any]:
    """Generate source-contract Finding instances across the public domain."""

    review_result = load_review_result_module()
    return st.builds(
        review_result.Finding,
        id=st.integers(
            min_value=1,
            max_value=(10**review_result.FINDING_ID_DIGITS) - 1,
        ).map(review_result.format_finding_id),
        concern=st.sampled_from(tuple(review_result.Concern)),
        severity=st.sampled_from(tuple(review_result.Severity)),
        file=st.text(min_size=1),
        line=st.integers(),
        rule=st.sampled_from(valid_rule_citations()),
        message=st.text(min_size=1),
        action=st.text(min_size=1),
    )


def review_results() -> st.SearchStrategy[Any]:
    """Generate source-contract ReviewResult instances."""

    review_result = load_review_result_module()
    return st.builds(
        review_result.ReviewResult,
        schema_version=st.just(review_result.SCHEMA_VERSION),
        findings=st.lists(review_findings()).map(tuple),
    )


def malformed_finding_ids() -> st.SearchStrategy[str]:
    """Generate the open complement of the source finding-id predicate."""

    review_result = load_review_result_module()
    return st.text(max_size=24).filter(
        lambda value: not review_result.is_valid_finding_id(value)
    )


def unknown_review_severity() -> str:
    """Derive a value outside the source-owned severity enum."""

    review_result = load_review_result_module()
    return f"{next(iter(review_result.Severity)).value}-unknown"


def unknown_review_concern() -> str:
    """Derive a value outside the source-owned concern enum."""

    review_result = load_review_result_module()
    return f"{next(iter(review_result.Concern)).value}-unknown"


def valid_rule_citations() -> tuple[str, ...]:
    """Return fixed independent citations spanning every supported family."""

    return tuple(case.citation for case in valid_rule_citation_cases())


def malformed_rule_citations() -> st.SearchStrategy[str]:
    """Generate variable malformed extensions of every valid citation family."""

    return st.tuples(
        st.sampled_from(valid_rule_citations()),
        st.text(min_size=1, max_size=80),
    ).map(lambda values: f"{values[0]}:{values[1]}")


def finding_without_required_field(field: str) -> dict[str, Any]:
    """Return a conforming finding with one source field removed."""

    finding = make_finding_dict()
    del finding[field]
    return finding

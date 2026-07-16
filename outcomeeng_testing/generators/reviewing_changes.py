"""Generated domains for review-changes evidence."""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st

from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_SPEC_PATH,
    REPO_ROOT,
    SKILL_FILE,
    load_review_result_module,
    make_finding_dict,
    review_rule_citations,
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
        rule=st.sampled_from(review_rule_citations()),
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
    """Return citations derived from every supported source family."""

    return review_rule_citations()


def malformed_rule_citations() -> st.SearchStrategy[str]:
    """Generate the open complement of the accepted citation-shape grammar."""

    review_result = load_review_result_module()
    return st.text(max_size=160).filter(
        lambda value: not review_result.is_supported_rule_citation_shape(value)
    )


def finding_without_required_field(field: str) -> dict[str, Any]:
    """Return a conforming finding with one source field removed."""

    finding = make_finding_dict()
    del finding[field]
    return finding


def changed_review_file_sets() -> tuple[list[str], list[str]]:
    """Return nested source-relevant changed-file sets for scope hashing."""

    first = [str(REVIEW_SPEC_PATH.relative_to(REPO_ROOT))]
    second = [
        *first,
        str(SKILL_FILE.relative_to(REPO_ROOT)),
    ]
    return first, second


def distinct_review_inputs() -> tuple[str, str]:
    """Return equal-scope review inputs with distinct content."""

    return (
        REVIEW_SPEC_PATH.read_text(encoding="utf-8"),
        SKILL_FILE.read_text(encoding="utf-8"),
    )

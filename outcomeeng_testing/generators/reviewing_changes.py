"""Generated domains for review-changes evidence."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any

from hypothesis import strategies as st

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REVIEW_RESULT_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "review-changes"
    / "scripts"
    / "review_result.py"
)
VALID_RULE_CITATIONS_FIXTURE = (
    REPO_ROOT
    / "outcomeeng_testing"
    / "fixtures"
    / "reviewing_changes"
    / "valid_rule_citations.json"
)


def load_review_result_module() -> ModuleType:
    """Load and cache the shipped review-result policy module."""

    cached = sys.modules.get("review_result")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "review_result",
        REVIEW_RESULT_MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load review_result from {REVIEW_RESULT_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_result"] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class RuleCitationCase:
    """One independent citation oracle paired with its source family."""

    family: Any
    citation: str


def valid_rule_citation_cases() -> tuple[RuleCitationCase, ...]:
    """Load fixed independent citation cases from the inert payload fixture."""

    review_result = load_review_result_module()
    payload = json.loads(VALID_RULE_CITATIONS_FIXTURE.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        raise RuntimeError(
            f"citation fixture must contain a cases array: {VALID_RULE_CITATIONS_FIXTURE}"
        )
    resolved: list[RuleCitationCase] = []
    for case in cases:
        if not isinstance(case, dict):
            raise RuntimeError(
                f"citation fixture case must be an object: {VALID_RULE_CITATIONS_FIXTURE}"
            )
        family = case.get("family")
        citation = case.get("citation")
        if not isinstance(family, str) or not isinstance(citation, str) or not citation:
            raise RuntimeError(
                f"citation fixture case requires family and citation strings: {VALID_RULE_CITATIONS_FIXTURE}"
            )
        resolved.append(
            RuleCitationCase(review_result.RuleCitationFamily(family), citation)
        )
    return tuple(resolved)


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


def make_finding_dict(
    *,
    finding_id: str | None = None,
    concern: Any | None = None,
    severity: Any | None = None,
    file_path: str | None = None,
    line: int | None = None,
    rule: str | None = None,
    message: str | None = None,
    action: str | None = None,
) -> dict[str, Any]:
    """Return one finding serialized through the production contract."""

    review_result = load_review_result_module()
    default_rule = valid_rule_citations()[0]
    finding = review_result.Finding(
        id=(
            finding_id
            if finding_id is not None
            else review_result.format_finding_id(review_result.SCHEMA_VERSION)
        ),
        concern=(concern if concern is not None else tuple(review_result.Concern)[-1]),
        severity=(
            severity if severity is not None else tuple(review_result.Severity)[-1]
        ),
        file=(
            file_path
            if file_path is not None
            else default_rule.split(":", maxsplit=1)[0]
        ),
        line=(line if line is not None else review_result.SCHEMA_VERSION),
        rule=(rule if rule is not None else valid_rule_citations()[3]),
        message=(
            message if message is not None else review_result.FINDING_MESSAGE_FIELD
        ),
        action=(action if action is not None else review_result.FINDING_ACTION_FIELD),
    )
    return review_result.finding_to_json_dict(finding)


def make_review_result_dict(
    *,
    findings: list[dict[str, Any]] | None = None,
    schema_version: int | None = None,
) -> dict[str, Any]:
    """Return a review-result mapping built from production field contracts."""

    review_result = load_review_result_module()
    return {
        review_result.DOCUMENT_SCHEMA_VERSION_FIELD: (
            schema_version
            if schema_version is not None
            else review_result.SCHEMA_VERSION
        ),
        review_result.DOCUMENT_FINDINGS_FIELD: (
            findings if findings is not None else [make_finding_dict()]
        ),
    }


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

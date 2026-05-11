"""Grade an audit verdict against expected structural fields.

The grader parses the assistant message as a single JSON document (the
verdict) and checks each expectation by recursive structural-subset
matching. Free-form prose has no role in the pass/fail decision; the
producing skill emits the verdict as its entire response per
``spx/15-audit-verdict-format.pdr.md``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from outcomeeng_evals.case import Case


@dataclass(frozen=True)
class GradeResult:
    """Outcome of grading a single trial."""

    passed: bool
    reasons: tuple[str, ...]


def parse_verdict(assistant_message: str) -> Any | None:
    """Return the parsed JSON verdict, or None if the message is not valid JSON.

    The verdict is the entire assistant response. Whitespace at the start
    or end of the response is tolerated; anything else is a parse error.
    """
    try:
        return json.loads(assistant_message.strip())
    except json.JSONDecodeError:
        return None


def grade(case: Case, assistant_message: str) -> GradeResult:
    """Compare the verdict in ``assistant_message`` to the case's expectations."""
    verdict = parse_verdict(assistant_message)
    if verdict is None:
        return GradeResult(
            passed=False, reasons=("verdict is not a parseable JSON document",)
        )

    reasons: list[str] = []
    for expected in case.must_contain:
        if not is_subset(expected, verdict):
            reasons.append(f"missing required structure {json.dumps(expected)}")
    for forbidden in case.must_not_contain:
        if is_subset(forbidden, verdict):
            reasons.append(f"forbidden structure present {json.dumps(forbidden)}")
    return GradeResult(passed=not reasons, reasons=tuple(reasons))


def is_subset(expected: Any, actual: Any) -> bool:
    """Return True when ``expected`` is a recursive structural subset of ``actual``.

    Semantics:

    - Dicts: every key in ``expected`` must exist in ``actual`` with a value
      that is itself a structural subset.
    - Lists: every element in ``expected`` must find at least one element in
      ``actual`` that is its structural subset (any-match, not positional).
    - Scalars: equality (``expected == actual``).
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and is_subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return all(any(is_subset(e, a) for a in actual) for e in expected)
    return bool(expected == actual)

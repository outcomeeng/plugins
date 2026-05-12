"""Grade an evaluated response against expected structural fields.

The grader parses the assistant message as a single JSON document and
checks each expectation by recursive structural-subset matching. Free-form
prose has no role in the pass/fail decision; the response format for a
given eval is declared by that eval's prompt.
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
    - Lists: multiset-match. Each expected element must match a distinct
      actual element under ``is_subset``; position-independent but
      cardinality-aware. ``[X, X]`` does not satisfy ``[X]`` — two expected
      Xs require two actual Xs. Greedy first-match consumption ordered by
      the expected list. The list path is O(len(expected) × len(actual))
      because each expected element rescans the unconsumed actual elements;
      that is fine for eval case files, so do not author large
      expected-list assertions.
    - Scalars: equality (``expected == actual``). Python's ``bool ==
      int`` semantics carry through — ``is_subset(True, 1)`` returns
      True because ``True == 1``. This matches the JSON structural
      intent: JSON ``true``/``false`` and JSON numbers share the
      integer comparison that ``==`` performs.
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and is_subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        # Multiset-match: greedy first-fit consumption. Each expected element
        # claims one distinct actual element; do not "fix" to any-match
        # (which would let two expected Xs both satisfy a single actual X).
        remaining = list(range(len(actual)))
        for element in expected:
            for index, actual_index in enumerate(remaining):
                if is_subset(element, actual[actual_index]):
                    remaining.pop(index)
                    break
            else:
                return False
        return True
    return bool(expected == actual)

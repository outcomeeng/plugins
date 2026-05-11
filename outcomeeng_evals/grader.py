"""Grade an audit verdict against expected structural fields.

The grader parses the XML verdict body and checks structural containment.
Free-form prose participates only as transcript context, never in the
pass/fail decision.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from outcomeeng_evals.case import Case, ExpectedElement


VERDICT_BLOCK = re.compile(
    r"<verdict\b[^>]*>.*?</verdict>",
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True)
class GradeResult:
    """Outcome of grading a single trial."""

    passed: bool
    reasons: tuple[str, ...]


def extract_verdict(assistant_message: str) -> str | None:
    """Return the first <verdict>...</verdict> XML block, or None if absent."""
    match = VERDICT_BLOCK.search(assistant_message)
    return match.group(0) if match else None


def grade(case: Case, assistant_message: str) -> GradeResult:
    """Compare the verdict found in ``assistant_message`` to the case's expectations."""
    verdict_xml = extract_verdict(assistant_message)
    if verdict_xml is None:
        return GradeResult(passed=False, reasons=("no <verdict> block in response",))

    try:
        root = ET.fromstring(verdict_xml)
    except ET.ParseError as exc:
        return GradeResult(passed=False, reasons=(f"verdict XML parse error: {exc}",))

    reasons: list[str] = []
    for expected in case.must_contain:
        if not _matches_any(root, expected):
            reasons.append(f"missing required element {_describe(expected)}")
    for forbidden in case.must_not_contain:
        if _matches_any(root, forbidden):
            reasons.append(f"forbidden element present {_describe(forbidden)}")

    return GradeResult(passed=not reasons, reasons=tuple(reasons))


def _matches_any(root: ET.Element, expected: ExpectedElement) -> bool:
    for elem in _walk(root):
        if elem.tag != expected.element:
            continue
        if all(elem.get(k) == v for k, v in expected.attributes.items()):
            return True
    return False


def _walk(elem: ET.Element) -> Iterator[ET.Element]:
    yield elem
    for child in elem:
        yield from _walk(child)


def _describe(expected: ExpectedElement) -> str:
    if not expected.attributes:
        return f"<{expected.element}>"
    attrs = " ".join(f'{k}="{v}"' for k, v in expected.attributes.items())
    return f"<{expected.element} {attrs}>"

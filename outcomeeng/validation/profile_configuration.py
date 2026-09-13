"""Reject independently authored native profile settings throughout source text."""

import re
from typing import Final

from outcomeeng.distribution.profiles import (
    MODEL_IDENTIFIER_PATTERN,
    NATIVE_CONFIGURATION_FIELDS,
)

_ASSIGNMENT: Final = re.compile(
    r"(?:^|[\s{,])['\"]?(?P<field>"
    + "|".join(re.escape(field) for field in sorted(NATIVE_CONFIGURATION_FIELDS))
    + r")[\"']?[ \t]*[:=][ \t]*(?=\S)"
)


def find_profile_literals(text: str) -> list[tuple[int, str]]:
    """Report native assignments and model literals without conditional exemptions."""
    violations: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        violations.extend(
            (line_number, match.group(0))
            for match in MODEL_IDENTIFIER_PATTERN.finditer(line)
        )
        violations.extend(
            (line_number, match.group("field")) for match in _ASSIGNMENT.finditer(line)
        )
    return violations

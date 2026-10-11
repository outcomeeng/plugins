"""Reject independently authored native profile settings throughout source text.

A native field is an authored assignment by the syntactic form of its binding
alone: an expression that reads a value or an interpolation placeholder binds
no authored value, while every other binding, a literal, a build template
token, or an unquoted value, does.
"""

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

_TEMPLATE_TOKEN: Final = re.compile(r"\{\{!")
_READ_EXPRESSION: Final = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*(?:[(\[]|\.[A-Za-z_])"
)
_INTERPOLATION_PLACEHOLDER: Final = re.compile(
    r"\{[A-Za-z0-9_.!:\[\]]*\}|%[sdrf(]|\$\{?[A-Za-z_]"
)


def _is_authored_binding(value: str) -> bool:
    """Decide from the binding's syntactic form whether it binds an authored value."""
    if _TEMPLATE_TOKEN.match(value):
        return True
    if _INTERPOLATION_PLACEHOLDER.match(value):
        return False
    return _READ_EXPRESSION.match(value) is None


def find_profile_literals(text: str) -> list[tuple[int, str]]:
    """Report native assignments and model literals without conditional exemptions."""
    violations: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        violations.extend(
            (line_number, match.group(0))
            for match in MODEL_IDENTIFIER_PATTERN.finditer(line)
        )
        violations.extend(
            (line_number, match.group("field"))
            for match in _ASSIGNMENT.finditer(line)
            if _is_authored_binding(line[match.end() :])
        )
    return violations

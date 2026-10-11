"""Binding forms and surrounding source contexts for native configuration fields.

Each tuple enumerates the forms of one branch of the configuration guard in
`outcomeeng.validation.profile_configuration`: its template-token branch, its
read-expression branch, its interpolation-placeholder branch, its
placeholder-joined-with-literal-text branch, and its assignment-boundary branch. Every build token comes from the delimiters and
`format_runtime_token` that `outcomeeng.distribution.contracts` owns.
"""

from typing import Final

from outcomeeng.distribution.contracts import (
    RUNTIME_TOKEN_FIELD_KIND,
    build_variable_token,
    format_runtime_token,
)
from outcomeeng.distribution.profiles import (
    AgentProfile,
    ClaudeEffort,
    CodexReasoningEffort,
    NATIVE_CONFIGURATION_FIELDS,
)

_LITERAL_BINDINGS: Final = ('"value"', "'value'")
"""Quoted literals: no template token, read expression, or placeholder opens them."""

LITERAL_BINDING: Final = _LITERAL_BINDINGS[0]
"""One quoted authored literal, the payload of a literal native assignment."""

PROFILE_DESCRIPTION_TOKEN: Final = build_variable_token(
    f"profile_description('{AgentProfile.STANDARD}')"
)
"""Build template token that renders the standard profile's description."""

_TEMPLATE_TOKEN_BINDINGS: Final = (
    PROFILE_DESCRIPTION_TOKEN,
    format_runtime_token(RUNTIME_TOKEN_FIELD_KIND, "value"),
)
"""Build template tokens: the guard's template-token branch."""

_UNQUOTED_IDENTIFIERS: Final = tuple(
    sorted(
        {
            str(value)
            for values in (CodexReasoningEffort, ClaudeEffort)
            for value in values
        }
    )
)
"""Identifier-shaped native values, taken from the enumerations that own them."""

_UNQUOTED_BINDINGS: Final = tuple(
    binding
    for identifier in _UNQUOTED_IDENTIFIERS
    for binding in (f"{identifier} (default)", f"{identifier}.")
)
"""Unquoted authored values: whitespace before a parenthesized word and a bare trailing dot."""

BARE_NAME_BINDINGS: Final = tuple(
    sorted(set(_UNQUOTED_IDENTIFIERS) | set(NATIVE_CONFIGURATION_FIELDS))
)
"""Bare names that read nothing: an effort value or a native field name, with no call, subscript, or attribute access."""

PLACEHOLDER_BINDINGS: Final = (
    "{name}",
    "{0}",
    "{}",
    "{name!r}",
    "{name:8}",
    "{item.key}",
    "{item[0]}",
    "%s",
    "%d",
    "%r",
    "%f",
    "%(name)s",
    "$name",
    "${name}",
)
"""Interpolation placeholders, each the whole bound value: brace, percent, and dollar forms."""

_LITERAL_JOINS: Final = (
    "{placeholder}-override",
    "{placeholder} for this run",
    "prefix-{placeholder}",
)

NEAR_PLACEHOLDER_BINDINGS: Final = tuple(
    join.format(placeholder=placeholder)
    for placeholder in PLACEHOLDER_BINDINGS
    for join in _LITERAL_JOINS
)
"""Placeholders joined with literal text, as a prefix or as a suffix: the value is no placeholder."""

AUTHORED_BINDINGS: Final = (
    _LITERAL_BINDINGS
    + _TEMPLATE_TOKEN_BINDINGS
    + _UNQUOTED_BINDINGS
    + BARE_NAME_BINDINGS
    + NEAR_PLACEHOLDER_BINDINGS
)
"""Bindings that carry an authored value: a literal, a build template token, an unquoted value, a bare name, or a placeholder joined with literal text."""

READ_BINDINGS: Final = (
    'lookup("key")',
    'settings["key"]',
    "settings.key",
    'settings.section.lookup("key")',
)
"""Bindings that read a value: a call, a subscript, or an attribute access."""

_ASSIGNMENT_BOUNDARIES: Final = (
    ("", ""),
    (" ", ""),
    ("    ", "  # trailing note"),
    (",", ""),
    ("{", "}"),
)

SURROUNDING_CONTEXTS: Final = _ASSIGNMENT_BOUNDARIES + (
    ("# ", ""),
    ("The configuration reads: ", "."),
)
"""Prefix and suffix pairs placing one binding in differing surrounding code.

The guard opens an assignment at line start, after whitespace, after a comma, or
after an opening brace; commentary and prose prefixes end in whitespace, so they
reach the same boundary.
"""

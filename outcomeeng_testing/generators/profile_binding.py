"""Binding forms and surrounding source contexts for native configuration fields."""

from typing import Final

from outcomeeng.distribution.profiles import AgentProfile

AUTHORED_BINDINGS: Final = (
    '"value"',
    "'value'",
    f"{{{{! profile_description('{AgentProfile.STANDARD}') !}}}}",
)
"""Bindings that carry an authored value: a literal or a build template token."""

READ_BINDINGS: Final = (
    'lookup("key")',
    'settings["key"]',
    "settings.key",
)
"""Bindings that read a value: a call, a subscript, or an attribute access."""

PLACEHOLDER_BINDINGS: Final = (
    "{name} for this run",
    "%s for this run",
    "${name} for this run",
)
"""Interpolation placeholders that open message text."""

SURROUNDING_CONTEXTS: Final = (
    ("", ""),
    ("# ", ""),
    ("    ", "  # trailing note"),
    ("The configuration reads: ", "."),
    ("{", "}"),
)
"""Prefix and suffix pairs placing one binding in differing surrounding code."""

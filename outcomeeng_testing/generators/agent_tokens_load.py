"""Generated load-failure cases for evidence of the agent-tokens data file a shipped script loads.

The cases derive from the loader module's own error vocabulary and the owner's declared
agent tokens, so the linked tests carry no failure wording and no token of their own.
Two nodes load the data file through the same loader and share these cases.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import ModuleType

from outcomeeng.distribution.contracts import declared_agent_tokens

VALID_TOKENS = declared_agent_tokens()
NON_OBJECT_DOCUMENT = json.dumps(list(VALID_TOKENS.values()))
MALFORMED_DOCUMENT = "{not json"


@dataclass(frozen=True)
class LoadFailureCase:
    """One state of the data file the loader cannot read tokens from, and the error line it opens with."""

    case_id: str
    tokens: str | None
    """The file's text, or ``None`` for an absent file."""
    make_directory: bool
    """Whether a directory stands at the file's path so reading it fails as unreadable."""
    expected_fragment: str


def load_failure_cases(module: ModuleType) -> tuple[LoadFailureCase, ...]:
    """Return one case per file state the loader reports as an ``error:`` line."""
    prefix = module.AGENT_TOKENS_ERROR_PREFIX
    return (
        LoadFailureCase(
            "absent", None, False, f"{prefix} {module.AGENT_TOKENS_NOT_FOUND}"
        ),
        LoadFailureCase(
            "unreadable", None, True, f"{prefix} {module.AGENT_TOKENS_UNREADABLE}"
        ),
        LoadFailureCase(
            "malformed",
            MALFORMED_DOCUMENT,
            False,
            f"{prefix} {module.AGENT_TOKENS_NOT_VALID_JSON}",
        ),
        LoadFailureCase(
            "non-object",
            NON_OBJECT_DOCUMENT,
            False,
            f"{prefix} {module.AGENT_TOKENS_NOT_AN_OBJECT}",
        ),
        *(
            LoadFailureCase(
                f"no-{VALID_TOKENS[missing]}",
                json.dumps(
                    {
                        key: token
                        for key, token in VALID_TOKENS.items()
                        if key != missing
                    }
                ),
                False,
                f"{prefix} {module.AGENT_TOKENS_LACKS_KEYS} {missing}: ",
            )
            for missing in module.AGENT_TOKENS_REQUIRED_KEYS
        ),
    )

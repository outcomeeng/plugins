"""Saved-login inputs constructed from the declared unsupported states."""

from dataclasses import dataclass
from typing import assert_never

from outcomeeng_testing.harnesses.discovery_auth import SavedLoginCondition
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    API_FIXTURE_PATH,
    FIXTURE_ROOT,
)


@dataclass(frozen=True)
class SavedLoginInput:
    document: str | None
    condition: SavedLoginCondition


def generated_saved_login_inputs() -> tuple[SavedLoginInput, ...]:
    """Enumerate absence, broken JSON, and a complete native API credential.

    The input construction determines the expected condition independently
    of the saved-login parser. The materialization harness receives only
    the document, never its expected condition.
    """
    initial = (FIXTURE_ROOT / "chatgpt.json").read_text(encoding="utf-8")
    api = API_FIXTURE_PATH.read_text(encoding="utf-8")
    rows: list[SavedLoginInput] = []
    for condition in SavedLoginCondition:
        match condition:
            case SavedLoginCondition.MISSING:
                document = None
            case SavedLoginCondition.MALFORMED:
                document = initial[: len(initial) // 2]
            case SavedLoginCondition.NON_SUBSCRIPTION:
                document = api
            case _:
                assert_never(condition)
        rows.append(SavedLoginInput(document, condition))
    return tuple(rows)

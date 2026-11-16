"""Property evidence: the owned-path alphabet rejects its open complement."""

from __future__ import annotations

from outcomeeng_evals.definition import OWNED_PATHS_FIELD
from outcomeeng_testing.harnesses.evals import (
    observe_owned_path_load,
    owned_path_property,
)


@owned_path_property(
    replay_test_name="test_owned_path_outside_the_alphabet_is_rejected"
)
def test_owned_path_outside_the_alphabet_is_rejected(owned_path: str) -> None:
    loaded = observe_owned_path_load(owned_path)

    assert loaded.definition is None, f"{owned_path!r} was accepted"
    assert loaded.error is not None
    assert OWNED_PATHS_FIELD in str(loaded.error)

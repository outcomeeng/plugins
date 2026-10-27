"""Compliance evidence for the coherence resolver's stale-base relay.

``l1``: the shipped resolver runs as a subprocess against a synthetic
repository whose origin is a real bare repository beside it.
"""

from __future__ import annotations

import json

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    base_advanced_after_branch_repo,
    remote_base_oid,
    run_coherence_scope,
)


def test_a_head_behind_the_fetched_base_is_relayed_as_the_stale_base_refusal() -> None:
    """The resolver relays the shared refusal instead of resolving a scope.

    Removing the relay makes the shared resolver's error escape as a
    traceback with a different exit code and no diagnostic line.
    """
    with base_advanced_after_branch_repo() as advanced:
        tip = remote_base_oid(advanced.repo, advanced.base_ref)

        completed = run_coherence_scope(advanced.repo, CHANGESET_SCOPE.HEAD_REF)

        assert completed.returncode == CHANGESET_SCOPE.EXIT_STALE_BASE
        assert not completed.stdout
        diagnostic = json.loads(completed.stderr.strip().splitlines()[-1])
        assert diagnostic[CHANGESET_SCOPE.StaleBaseField.STATUS] == (
            CHANGESET_SCOPE.STALE_BASE_STATUS
        )
        assert diagnostic[CHANGESET_SCOPE.StaleBaseField.TIP] == tip

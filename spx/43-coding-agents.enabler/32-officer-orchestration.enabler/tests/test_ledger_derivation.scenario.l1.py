"""Reachability evidence for the officer-ledger derivation entry point."""

from typing import cast

from outcomeeng_testing.harnesses.officer_orchestration import (
    run_ledger,
)


def test_entrypoint_returns_the_minimum_versioned_ledger() -> None:
    """The shipped entry point is executable and pins its minimum result shape."""
    observation = run_ledger(
        ["derive"],
        {
            "schemaVersion": 1,
            "change": "owner/changes#123",
            "mailRecords": [],
            "journalRuns": [],
        },
    )
    result = observation.result
    ledger = cast(dict[str, object], result["ledger"])

    assert observation.parameters == ("argv", "stdin", "stdout", "stderr")
    assert observation.exit_code == 0
    assert observation.stderr == ""
    assert set(result) == {"ledger", "schemaVersion", "status"}
    assert result["schemaVersion"] == 1
    assert result["status"] == "succeeded"
    assert set(ledger) == {
        "change",
        "findingProvenance",
        "heads",
        "passes",
        "reads",
        "runningSpend",
        "verdicts",
        "wallTimeSeconds",
    }
    assert ledger["change"] == "owner/changes#123"
    assert ledger["passes"] == []
    assert ledger["heads"] == []
    assert ledger["verdicts"] == []
    assert ledger["findingProvenance"] == []
    assert ledger["reads"] == []
    assert ledger["runningSpend"] == {}
    assert ledger["wallTimeSeconds"] == 0

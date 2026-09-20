"""Reachability evidence for the officer-ledger derivation entry point."""

from typing import cast

from outcomeeng_testing.harnesses.officer_orchestration import (
    run_empty_source_ledger,
)


def test_entrypoint_returns_the_minimum_versioned_ledger() -> None:
    """The shipped entry point is executable and pins its minimum result shape."""
    observation = run_empty_source_ledger()
    module = observation.module
    result = observation.result
    ledger = cast(dict[str, object], result[module.LEDGER_FIELD])

    assert observation.parameters == module.ENTRYPOINT_PARAMETER_NAMES
    assert observation.exit_code == module.SUCCESS_EXIT_CODE
    assert observation.stderr == ""
    assert set(result) == set(module.RESULT_FIELDS)
    assert result[module.SCHEMA_VERSION_FIELD] == module.SCHEMA_VERSION
    assert result[module.STATUS_FIELD] == module.SUCCEEDED_STATUS
    assert set(ledger) == set(module.LEDGER_FIELDS)
    assert ledger[module.CHANGE_FIELD] == module.EMPTY_SOURCE_SAMPLE_CHANGE
    for field_name in module.EMPTY_LEDGER_SEQUENCE_FIELDS:
        assert ledger[field_name] == []
    assert ledger[module.RUNNING_SPEND_FIELD] == {}
    assert ledger[module.WALL_TIME_SECONDS_FIELD] == 0

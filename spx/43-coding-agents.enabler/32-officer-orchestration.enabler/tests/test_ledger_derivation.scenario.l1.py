"""Reachability evidence for the officer-ledger derivation entry point."""

from __future__ import annotations

import importlib.util
import inspect
import io
import json
from pathlib import Path
from types import ModuleType

REPOSITORY_ROOT = Path(__file__).parents[4]
SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "src/plugins/coding-agents/skills/orchestrate-officers/scripts/derive_ledger.py"
)
MODULE_NAME = "orchestrate_officers_derive_ledger"
EXPECTED_ENTRYPOINT_PARAMETERS = ("argv", "stdin", "stdout", "stderr")
EXPECTED_RESULT_KEYS = {"schemaVersion", "status", "ledger"}
EXPECTED_LEDGER_KEYS = {
    "change",
    "passes",
    "heads",
    "verdicts",
    "findingProvenance",
    "reads",
    "runningSpend",
    "wallTimeSeconds",
}


def _load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT_PATH)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_entrypoint_returns_the_minimum_versioned_ledger() -> None:
    """The shipped entry point is executable and pins its minimum result shape."""
    module = _load_script()
    parameters = tuple(inspect.signature(module.main).parameters)
    standard_input = io.StringIO(
        json.dumps(
            {
                "schemaVersion": 1,
                "change": "outcomeeng/changes#88",
                "mailRecords": [],
                "journalRuns": [],
            }
        )
    )
    standard_output = io.StringIO()
    standard_error = io.StringIO()

    exit_code = module.main(
        ["derive"],
        stdin=standard_input,
        stdout=standard_output,
        stderr=standard_error,
    )

    result = json.loads(standard_output.getvalue())
    assert parameters == EXPECTED_ENTRYPOINT_PARAMETERS
    assert exit_code == 0
    assert standard_error.getvalue() == ""
    assert set(result) == EXPECTED_RESULT_KEYS
    assert result["schemaVersion"] == module.SCHEMA_VERSION
    assert result["status"] == "succeeded"
    assert set(result["ledger"]) == EXPECTED_LEDGER_KEYS
    assert result["ledger"] == {
        "change": "outcomeeng/changes#88",
        "passes": [],
        "heads": [],
        "verdicts": [],
        "findingProvenance": [],
        "reads": [],
        "runningSpend": {},
        "wallTimeSeconds": 0,
    }

"""Test infrastructure for the officer-ledger derivation entry point."""

from __future__ import annotations

import importlib.util
import inspect
import io
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TextIO, cast

REPOSITORY_ROOT = Path(__file__).parents[2]
LEDGER_SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "src/plugins/coding-agents/skills/orchestrate-officers/scripts/derive_ledger.py"
)
LEDGER_MODULE_NAME = "coding_agents_officer_ledger"


class LedgerModule(Protocol):
    """Source-owned ledger contract exposed through the shipped module."""

    SCHEMA_VERSION: int
    SCHEMA_VERSION_FIELD: str
    CHANGE_FIELD: str
    MAIL_RECORDS_FIELD: str
    JOURNAL_RUNS_FIELD: str
    STATUS_FIELD: str
    DETAIL_FIELD: str
    LEDGER_FIELD: str
    FINDING_PROVENANCE_FIELD: str
    RUNNING_SPEND_FIELD: str
    WALL_TIME_SECONDS_FIELD: str
    PASSES_FIELD: str
    HEADS_FIELD: str
    VERDICTS_FIELD: str
    READS_FIELD: str
    SUCCEEDED_STATUS: str
    INVALID_INPUT_STATUS: str
    DERIVE_OPERATION: str
    SUCCESS_EXIT_CODE: int
    INVALID_INPUT_EXIT_CODE: int

    def main(
        self,
        argv: Sequence[str] | None = None,
        *,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> int: ...


@dataclass(frozen=True)
class LedgerEntrypointObservation:
    """Captured public entry-point output with its source contract."""

    parameters: tuple[str, ...]
    exit_code: int
    result: dict[str, object]
    stderr: str


def load_ledger_module() -> LedgerModule:
    """Load the shipped ledger entry point from the authored skill surface."""
    specification = importlib.util.spec_from_file_location(
        LEDGER_MODULE_NAME, LEDGER_SCRIPT_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Cannot load ledger module: {LEDGER_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return cast(LedgerModule, module)


def run_ledger(
    arguments: Sequence[str], payload: Mapping[str, object] | str
) -> LedgerEntrypointObservation:
    """Execute the ledger entry point and capture its observations."""
    module = load_ledger_module()
    standard_output = io.StringIO()
    standard_error = io.StringIO()
    standard_input = payload if isinstance(payload, str) else json.dumps(payload)
    exit_code = module.main(
        arguments,
        stdin=io.StringIO(standard_input),
        stdout=standard_output,
        stderr=standard_error,
    )
    return LedgerEntrypointObservation(
        parameters=tuple(inspect.signature(module.main).parameters),
        exit_code=exit_code,
        result=cast(dict[str, object], json.loads(standard_output.getvalue())),
        stderr=standard_error.getvalue(),
    )

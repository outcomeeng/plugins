"""Test infrastructure for the officer-ledger derivation entry point."""

from __future__ import annotations

import importlib.util
import inspect
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

REPOSITORY_ROOT = Path(__file__).parents[2]
LEDGER_SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "src/plugins/coding-agents/skills/orchestrate-officers/scripts/derive_ledger.py"
)
LEDGER_MODULE_NAME = "coding_agents_officer_ledger"


@dataclass(frozen=True)
class LedgerEntrypointObservation:
    """Captured public entry-point output with its source contract."""

    module: ModuleType
    parameters: tuple[str, ...]
    exit_code: int
    result: dict[str, object]
    stderr: str


def load_ledger_module() -> ModuleType:
    """Load the shipped ledger entry point from the authored skill surface."""
    specification = importlib.util.spec_from_file_location(
        LEDGER_MODULE_NAME, LEDGER_SCRIPT_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Cannot load ledger module: {LEDGER_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def run_empty_source_ledger() -> LedgerEntrypointObservation:
    """Invoke the documented empty-source interaction and capture observations."""
    module = load_ledger_module()
    standard_output = io.StringIO()
    standard_error = io.StringIO()
    exit_code = module.main(
        list(module.DERIVE_ARGUMENTS),
        stdin=io.StringIO(json.dumps(module.empty_source_request())),
        stdout=standard_output,
        stderr=standard_error,
    )
    return LedgerEntrypointObservation(
        module=module,
        parameters=tuple(inspect.signature(module.main).parameters),
        exit_code=exit_code,
        result=cast(dict[str, object], json.loads(standard_output.getvalue())),
        stderr=standard_error.getvalue(),
    )

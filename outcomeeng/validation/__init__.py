"""Signal-safe quality-gate orchestrator for the marketplace.

Public surface:

- `Step` — frozen dataclass naming a step's label and argv
- `STEPS` — the declared step list
- `ProcessHandle`, `ProcessSpawner` — DI Protocols for subprocess creation
- `ProductionSpawner` — real `subprocess.Popen` adapter
- `run` — orchestration entry point
"""

from __future__ import annotations

from outcomeeng.validation._engine import run
from outcomeeng.validation._model import (
    ProcessHandle,
    ProcessSpawner,
    Step,
)
from outcomeeng.validation._spawner import ProductionSpawner
from outcomeeng.validation._steps import (
    ACTIONLINT_ARGV,
    HOOK_SAFETY_ARGV,
    MYPY_ARGV,
    PYRIGHT_ARGV,
    PYTHON_SOURCE_PATHS,
    PYTEST_ARGV,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SHELLCHECK_ARGV,
    SPX_MARKDOWN_ARGV,
    STEPS,
)

__all__ = [
    "ACTIONLINT_ARGV",
    "HOOK_SAFETY_ARGV",
    "MYPY_ARGV",
    "PYRIGHT_ARGV",
    "PYTHON_SOURCE_PATHS",
    "PYTEST_ARGV",
    "RUFF_CHECK_ARGV",
    "RUFF_FORMAT_ARGV",
    "SHELLCHECK_ARGV",
    "SPX_MARKDOWN_ARGV",
    "STEPS",
    "ProcessHandle",
    "ProcessSpawner",
    "ProductionSpawner",
    "Step",
    "run",
]

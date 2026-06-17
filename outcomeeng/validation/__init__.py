"""Signal-safe quality-gate orchestrator for the marketplace.

Public surface:

- `Step` — frozen dataclass naming a step's label and argv
- `STEPS` — the declared step list
- `*_ARGV` and output-label constants — source-owned values imported by tests
- `ProcessHandle`, `ProcessSpawner` — DI Protocols for subprocess creation
- `ProductionSpawner` — real `subprocess.Popen` adapter
- `run` — orchestration entry point
"""

from __future__ import annotations

from outcomeeng.validation._engine import (
    FAILURE_EXCERPT_LINE_LIMIT,
    FULL_LOG_LABEL,
    STEP_FAIL_STATUS,
    STEP_PASS_STATUS,
    run,
)
from outcomeeng.validation._model import (
    ProcessHandle,
    ProcessSpawner,
    Step,
)
from outcomeeng.validation._spawner import ProductionSpawner
from outcomeeng.validation._steps import (
    ACTIONLINT_ARGV,
    HOOK_SAFETY_ARGV,
    FMT_CHECK_ARGV,
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
    "FMT_CHECK_ARGV",
    "FAILURE_EXCERPT_LINE_LIMIT",
    "FULL_LOG_LABEL",
    "MYPY_ARGV",
    "PYRIGHT_ARGV",
    "PYTHON_SOURCE_PATHS",
    "PYTEST_ARGV",
    "RUFF_CHECK_ARGV",
    "RUFF_FORMAT_ARGV",
    "SHELLCHECK_ARGV",
    "SPX_MARKDOWN_ARGV",
    "STEPS",
    "STEP_FAIL_STATUS",
    "STEP_PASS_STATUS",
    "ProcessHandle",
    "ProcessSpawner",
    "ProductionSpawner",
    "Step",
    "run",
]

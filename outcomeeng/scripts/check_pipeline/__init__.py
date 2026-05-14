"""Signal-safe quality-gate orchestrator for the marketplace.

Public surface:

- `Step` — frozen dataclass naming a step's label and argv
- `STEPS` — the declared step list
- `ProcessHandle`, `ProcessSpawner` — DI Protocols for subprocess creation
- `ProductionSpawner` — real `subprocess.Popen` adapter
- `run` — orchestration entry point
"""

from __future__ import annotations

from outcomeeng.scripts.check_pipeline._model import (
    ProcessHandle,
    ProcessSpawner,
    Step,
)
from outcomeeng.scripts.check_pipeline._runner import run
from outcomeeng.scripts.check_pipeline._spawner import ProductionSpawner
from outcomeeng.scripts.check_pipeline._steps import STEPS

__all__ = [
    "STEPS",
    "ProcessHandle",
    "ProcessSpawner",
    "ProductionSpawner",
    "Step",
    "run",
]

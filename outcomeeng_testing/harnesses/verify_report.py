"""Standard-subprocess harness for the /verify report script.

Backs the reachability tests of the verify-skill Node. The harness writes the
supplied result records as JSON into a temporary directory it owns, runs the
shipped script on that file with the current interpreter, and exposes the exit
code, stdout, and stderr as an observation. It decides nothing: every predicate
belongs to the linked test.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, Final

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SCRIPT: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "product-tree"
    / "skills"
    / "verify"
    / "scripts"
    / "render_report.py"
)
RESULTS_FILE: Final = "results.json"


@dataclass(frozen=True)
class Run:
    """What one run of the script printed and returned."""

    exit_code: int
    stdout: str
    stderr: str


def load_script() -> ModuleType:
    """Load the shipped script as a module, for its source-owned names."""
    spec = importlib.util.spec_from_file_location("verify_render_report", SCRIPT)
    if spec is None or spec.loader is None:
        msg = f"cannot load {SCRIPT}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(records: Any) -> Run:
    """Run the script on ``records`` written as JSON to a file it reads by path."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / RESULTS_FILE
        path.write_text(json.dumps(records), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
    return Run(completed.returncode, completed.stdout, completed.stderr)

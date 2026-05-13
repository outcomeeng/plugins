"""Shared scaffolding for the verdict-toolchain scenario tests.

Collapses three pieces of duplication that appeared in every test file
in this directory:

- ``SCRIPTS_DIR`` and the per-script paths derived from it. Every file
  previously walked ``__file__.parents[5]`` to find the marketplace's
  ``plugins/spec-tree/skills/auditing/scripts`` directory. A single
  module-level constant is the canonical source.
- ``JSON_BLOCK_BEGIN`` / ``JSON_BLOCK_END``. The HTML-comment
  delimiters used by ``markdown+json`` were hardcoded as string
  literals in the test files that inspect the carrier. Importing them
  from ``verdict.py`` (the production module that defines them) means
  the tests cannot disagree with the producer/consumer toolchain about
  the delimiter pair — there is exactly one definition.
- ``run_script``. Every file wrote a thin ``subprocess.run`` wrapper
  with identical defaults (``capture_output=True``, ``text=True``,
  optional stdin). One helper covers them all.

``conftest.py`` is the right home because:

- Pytest discovers it automatically and adds its directory to
  ``sys.path`` for the duration of the test session, so test modules
  can ``from conftest import ...`` without further configuration.
- Constants and helpers shared across test files belong with their
  test directory, not in the production tree (this file is co-located
  with the tests under ``spx/`` per the durable-map convention).
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
from types import ModuleType

# Five ``parents`` hops land at the repository root: tests directory ->
# verdict-toolchain.enabler -> evidence.enabler -> spec-tree.enabler ->
# spx -> repo root. The walk depends on the on-disk layout; if the
# tests are ever moved, this constant moves with them.
SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[5]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "auditing"
    / "scripts"
)

VERDICT_MODULE_PATH = SCRIPTS_DIR / "verdict.py"
EMIT_SCRIPT = SCRIPTS_DIR / "emit_verdict.py"
READ_SCRIPT = SCRIPTS_DIR / "read_verdict.py"
AGGREGATE_SCRIPT = SCRIPTS_DIR / "aggregate_verdicts.py"
PASS_RESULTS_SCRIPT = SCRIPTS_DIR / "pass_results.py"


def load_verdict_module() -> ModuleType:
    """Load ``verdict.py`` as a module and cache it under ``sys.modules``.

    The verdict module is not importable as a package — it lives under
    ``plugins/`` (a runtime-substituted plugin directory) and the
    marketplace deliberately ships every script under ``scripts/`` as a
    bare module that ``python3 path/to/script.py`` invocations resolve
    via ``sys.path[0]``. Tests that need to introspect the dataclasses,
    constants, or rollup logic load it through ``importlib`` instead of
    a regular import.

    Returns the already-loaded module on subsequent calls so the
    importlib loader runs at most once per test session.
    """
    cached = sys.modules.get("verdict")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("verdict", VERDICT_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {VERDICT_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["verdict"] = module
    spec.loader.exec_module(module)
    return module


# Load once at conftest import so ``JSON_BLOCK_BEGIN`` / ``JSON_BLOCK_END``
# come from the production module. A test file that hardcodes the
# delimiter strings could drift from the producer/consumer; this import
# closes that gap.
_verdict = load_verdict_module()
JSON_BLOCK_BEGIN: str = _verdict.JSON_BLOCK_BEGIN
JSON_BLOCK_END: str = _verdict.JSON_BLOCK_END


def run_script(
    script: pathlib.Path,
    *args: str,
    stdin: str | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Invoke a toolchain script as a subprocess and return the result.

    Every test in this directory exercises its target via
    ``subprocess.run`` with the same flags: capture stdout/stderr, text
    mode, and an optional stdin payload. ``check=False`` is the default
    because most tests inspect the returncode explicitly; tests that
    expect success can pass ``check=True`` to fail fast.
    """
    return subprocess.run(
        [sys.executable, str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=check,
    )

"""Harness for verdict-toolchain scenario tests.

Provides the shared scaffolding consumed by every test file under
``spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler/tests/``:

- ``SCRIPTS_DIR`` and the per-script paths derived from it. Without a single
  source, every test file walks ``__file__.parents[...]`` to find
  ``src/plugins/spec-tree/skills/audit/scripts``.
- ``JSON_BLOCK_BEGIN`` / ``JSON_BLOCK_END``. The HTML-comment delimiters used
  by ``markdown+json`` are defined in ``verdict.py`` (the production module).
  Importing them here means tests cannot disagree with the producer/consumer
  toolchain about the delimiter pair — there is exactly one definition.
- ``run_script``. A thin ``subprocess.run`` wrapper with the defaults every
  test uses (``capture_output=True``, ``text=True``, optional stdin).

The harness lives in ``outcomeeng_testing/harnesses/`` per
``spx/15-test-infrastructure.pdr.md`` — shared test scaffolding is production
code with its home outside ``tests/`` and outside ``spx/``.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
from types import ModuleType

# Two ``parents`` hops land at the repository root: this file lives at
# ``outcomeeng_testing/harnesses/verdict_toolchain.py``.
SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[2]
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "audit"
    / "scripts"
)

VERDICT_MODULE_PATH = SCRIPTS_DIR / "verdict.py"
EMIT_SCRIPT = SCRIPTS_DIR / "emit_verdict.py"
READ_SCRIPT = SCRIPTS_DIR / "read_verdict.py"
AGGREGATE_SCRIPT = SCRIPTS_DIR / "aggregate_verdicts.py"
PASS_RESULTS_SCRIPT = SCRIPTS_DIR / "pass_results.py"
AUDIT_ORCHESTRATOR_SCRIPT = SCRIPTS_DIR / "audit_orchestrator.py"


def load_verdict_module() -> ModuleType:
    """Load ``verdict.py`` as a module and cache it under ``sys.modules``.

    The verdict module is not importable as a package — it lives under
    ``src/plugins/`` (the authored plugin source directory) and the
    marketplace deliberately ships every script under ``scripts/`` as a bare
    module that ``python3 path/to/script.py`` invocations resolve via
    ``sys.path[0]``.
    Tests that need to introspect the dataclasses, constants, or rollup logic
    load it through ``importlib`` instead of a regular import.

    Returns the already-loaded module on subsequent calls so the importlib
    loader runs at most once per test session.
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


# Load once at module import so ``JSON_BLOCK_BEGIN`` / ``JSON_BLOCK_END`` come
# from the production module. A test file that hardcodes the delimiter
# strings could drift from the producer/consumer; this import closes that gap.
_verdict = load_verdict_module()
JSON_BLOCK_BEGIN: str = _verdict.JSON_BLOCK_BEGIN
JSON_BLOCK_END: str = _verdict.JSON_BLOCK_END


def run_script(
    script: pathlib.Path,
    *args: str,
    stdin: str | None = None,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke a toolchain script as a subprocess and return the result.

    Every test in the verdict-toolchain suite exercises its target via
    ``subprocess.run`` with the same flags: capture stdout/stderr, text mode,
    and an optional stdin payload. ``check=False`` is the default because most
    tests inspect the returncode explicitly; tests that expect success can
    pass ``check=True`` to fail fast.

    ``env``, when provided, is the complete environment passed to the child
    process — pass ``{**os.environ, "PYTHONHASHSEED": "0"}`` to derive from
    the caller's environment. ``None`` (the default) inherits the caller's
    environment unchanged. Tests that need to control hash randomization or
    other environment-driven determinism set this explicitly.
    """
    return subprocess.run(
        [sys.executable, str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=check,
        env=env,
    )

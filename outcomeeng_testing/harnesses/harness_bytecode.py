"""Resource lifecycle and observations for harness-bytecode evidence.

Every function here starts a real fresh interpreter or lists a fixture
directory and returns what it observed. The predicate that decides pass or fail
belongs to the linked test.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import outcomeeng_testing.harnesses as harnesses_package
from outcomeeng.distribution.contracts import DIST_DIR_NAME

HARNESS_DIRECTORY = Path(harnesses_package.__file__).parent
REPOSITORY_ROOT = HARNESS_DIRECTORY.parent.parent
FIXTURE_DIRECTORY = HARNESS_DIRECTORY.parent / "fixtures" / "harness_bytecode"
VIOLATING_DIRECTORY = FIXTURE_DIRECTORY / "violating"
CONFORMING_DIRECTORY = FIXTURE_DIRECTORY / "conforming"
SHIPPED_SCRIPT_FIXTURE = FIXTURE_DIRECTORY / "shipped_script.py.txt"
SHIPPED_SCRIPT_NAME = "shipped_script.py"

CACHE_DIRECTORY_NAME = "__pycache__"
BYTECODE_SUFFIX = ".pyc"

_FLAG_PROGRAM = (
    f"import {harnesses_package.__name__}, sys; print(sys.dont_write_bytecode)"
)
_LOAD_PROGRAM = (
    "import sys; from pathlib import Path; "
    "from outcomeeng.distribution.shipped_scripts import load_shipped_module; "
    "load_shipped_module('harness_bytecode_fixture_script', Path(sys.argv[1]))"
)


def violating_launch_fixtures() -> tuple[Path, ...]:
    """Fixture sources whose script launches leave bytecode writing on."""
    return tuple(sorted(VIOLATING_DIRECTORY.glob("*.py.txt")))


def conforming_launch_fixtures() -> tuple[Path, ...]:
    """Fixture sources whose launches leave no bytecode behind."""
    return tuple(sorted(CONFORMING_DIRECTORY.glob("*.py.txt")))


def harness_module_paths() -> tuple[Path, ...]:
    """Every harness module under the harness package directory."""
    return tuple(sorted(HARNESS_DIRECTORY.glob("*.py")))


def bytecode_entries_under_dist() -> tuple[str, ...]:
    """Repository-relative path of every ``__pycache__`` directory and ``.pyc`` file under ``dist/``."""
    distribution = REPOSITORY_ROOT / DIST_DIR_NAME
    return tuple(
        sorted(
            str(path.relative_to(REPOSITORY_ROOT))
            for path in distribution.rglob("*")
            if path.name == CACHE_DIRECTORY_NAME or path.suffix == BYTECODE_SUFFIX
        )
    )


def _fresh_interpreter(program: str, *arguments: str) -> str:
    """Run ``program`` in a fresh interpreter that inherits no bytecode setting."""
    completed = subprocess.run(
        [sys.executable, "-c", program, *arguments],
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": "", "PYTHONDONTWRITEBYTECODE": ""},
        cwd=REPOSITORY_ROOT,
    )
    return completed.stdout


def fresh_import_bytecode_flag() -> bool:
    """The ``sys.dont_write_bytecode`` value after a fresh interpreter imports the harness package."""
    return bool(ast.literal_eval(_fresh_interpreter(_FLAG_PROGRAM).strip()))


def entries_beside_script_after_load() -> tuple[str, ...]:
    """Names standing beside a script copy after a fresh interpreter loads it as a shipped script."""
    with TemporaryDirectory() as directory:
        script = Path(directory) / SHIPPED_SCRIPT_NAME
        script.write_text(
            SHIPPED_SCRIPT_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
        )
        _fresh_interpreter(_LOAD_PROGRAM, str(script))
        return tuple(
            sorted(path.name for path in Path(directory).iterdir() if path != script)
        )

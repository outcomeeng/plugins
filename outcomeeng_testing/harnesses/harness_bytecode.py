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

HARNESS_DIRECTORY = Path(harnesses_package.__file__).parent
REPOSITORY_ROOT = HARNESS_DIRECTORY.parent.parent
FIXTURE_DIRECTORY = HARNESS_DIRECTORY.parent / "fixtures" / "harness_bytecode"
VIOLATING_DIRECTORY = FIXTURE_DIRECTORY / "violating"
CONFORMING_DIRECTORY = FIXTURE_DIRECTORY / "conforming"
SHIPPED_SCRIPT_FIXTURE = FIXTURE_DIRECTORY / "shipped_script.py.txt"
SHIPPED_SCRIPT_NAME = "shipped_script.py"

GUARD_OFF_DIRECTORY = FIXTURE_DIRECTORY / "guard_off"
UNGUARDED_PACKAGE_FIXTURE = GUARD_OFF_DIRECTORY / "package_init.py.txt"
UNGUARDED_LOADER_FIXTURE = GUARD_OFF_DIRECTORY / "script_loader.py.txt"
UNGUARDED_PACKAGE_NAME = "unguarded_harnesses"
UNGUARDED_LOADER_NAME = "unguarded_script_loader"

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


def unguarded_import_bytecode_flag() -> bool:
    """The ``sys.dont_write_bytecode`` value after a fresh interpreter imports a package whose import leaves bytecode writing as found."""
    with TemporaryDirectory() as directory:
        package = Path(directory) / UNGUARDED_PACKAGE_NAME
        package.mkdir()
        (package / "__init__.py").write_text(
            UNGUARDED_PACKAGE_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
        )
        program = (
            f"import sys; sys.path.insert(0, {directory!r}); "
            f"import {UNGUARDED_PACKAGE_NAME}; print(sys.dont_write_bytecode)"
        )
        return bool(ast.literal_eval(_fresh_interpreter(program).strip()))


def _names_beside_script(directory: str, script: Path) -> tuple[str, ...]:
    return tuple(
        sorted(path.name for path in Path(directory).iterdir() if path != script)
    )


def _stage_script(directory: str) -> Path:
    script = Path(directory) / SHIPPED_SCRIPT_NAME
    script.write_text(
        SHIPPED_SCRIPT_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return script


def entries_beside_script_after_load() -> tuple[str, ...]:
    """Names standing beside a script copy after a fresh interpreter loads it as a shipped script."""
    with TemporaryDirectory() as directory:
        script = _stage_script(directory)
        _fresh_interpreter(_LOAD_PROGRAM, str(script))
        return _names_beside_script(directory, script)


def unguarded_entries_beside_script_after_load() -> tuple[str, ...]:
    """Names standing beside a script copy after a fresh interpreter loads it through a loader that leaves bytecode writing as found."""
    with TemporaryDirectory() as script_directory, TemporaryDirectory() as loader_directory:
        script = _stage_script(script_directory)
        loader = Path(loader_directory) / f"{UNGUARDED_LOADER_NAME}.py"
        loader.write_text(
            UNGUARDED_LOADER_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
        )
        program = (
            f"import sys; sys.path.insert(0, {loader_directory!r}); "
            f"from {UNGUARDED_LOADER_NAME} import load; "
            f"from pathlib import Path; "
            f"load('harness_bytecode_unguarded_script', Path(sys.argv[1]))"
        )
        _fresh_interpreter(program, str(script))
        return _names_beside_script(script_directory, script)

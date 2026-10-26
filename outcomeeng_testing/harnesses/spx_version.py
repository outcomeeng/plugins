"""An `spx` executable path that names no file, for the version-floor gate step."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.spx_version import SPX_EXECUTABLE


def absent_spx_executable(directory: Path) -> str:
    """Return a path to an `spx` executable inside ``directory`` that does not exist."""

    executable = directory / SPX_EXECUTABLE
    if executable.exists():
        raise FileExistsError(executable)
    return str(executable)

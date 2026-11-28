"""Observations of the Hypothesis profiles a pytest run of this repository loads."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from hypothesis import settings

from outcomeeng_testing.harnesses.real_agent_selection import REPOSITORY_ROOT

PROFILE_EXAMPLES_FUNCTION: Final = "profile_examples"
MAX_EXAMPLES_KEYWORD: Final = "max_examples"
# The trees whose Python modules declare example counts: the test
# infrastructure package and every test file under the Product Tree.
EXAMPLE_COUNT_ROOTS: Final = ("outcomeeng_testing", "spx")
# The module that registers the profiles states their counts itself.
PROFILE_REGISTRY_PATH: Final = "outcomeeng_testing/hypothesis_profiles.py"
PYTHON_SUFFIX: Final = ".py"
PYPROJECT_NAME: Final = "pyproject.toml"
RUN_TIMEOUT_SECONDS: Final = 120
PROBE_MARKER: Final = "HYPOTHESIS_PROFILE_PROBE "
PROBE_TEST_NAME: Final = "test_profile_probe.py"
PROBE_TEST_SOURCE: Final = (
    "import json\n"
    "from hypothesis import settings\n\n"
    "def test_profile_probe() -> None:\n"
    "    observed = {\n"
    "        'profile': settings.get_current_profile_name(),\n"
    "        'max_examples': settings.default.max_examples,\n"
    "    }\n"
    f"    print({PROBE_MARKER!r} + json.dumps(observed))\n"
)


@dataclass(frozen=True)
class LoadedProfile:
    """The profile one real pytest run of the repository configuration loaded."""

    exit_code: int
    profile: str | None
    example_count: int | None
    output: str


def loaded_profile(*pytest_arguments: str) -> LoadedProfile:
    """Run one probe test under the repository's pytest configuration.

    The probe lives in a scratch directory and the run reads the repository's
    `pyproject.toml`, so its `addopts` decide which modules load before the
    probe reads the Hypothesis profile in force.
    """

    with TemporaryDirectory() as tmp:
        probe = Path(tmp) / PROBE_TEST_NAME
        probe.write_text(PROBE_TEST_SOURCE, encoding="utf-8")
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-s",
                "-p",
                "no:cacheprovider",
                "-c",
                str(REPOSITORY_ROOT / PYPROJECT_NAME),
                "--rootdir",
                str(REPOSITORY_ROOT),
                *pytest_arguments,
                str(probe),
            ),
            cwd=REPOSITORY_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            check=False,
        )
    reported = [
        json.loads(line.split(PROBE_MARKER, maxsplit=1)[1])
        for line in completed.stdout.splitlines()
        if PROBE_MARKER in line
    ]
    observed = reported[0] if reported else {}
    return LoadedProfile(
        exit_code=completed.returncode,
        profile=observed.get("profile"),
        example_count=observed.get("max_examples"),
        output=completed.stdout + completed.stderr,
    )


@contextmanager
def profile_loaded(name: str) -> Iterator[None]:
    """Load the Hypothesis profile ``name`` and restore the one in force after."""

    previous = settings.get_current_profile_name()
    settings.load_profile(name)
    try:
        yield
    finally:
        settings.load_profile(previous)


def unrouted_example_counts(root: Path = REPOSITORY_ROOT) -> tuple[str, ...]:
    """Return each ``max_examples`` argument that bypasses ``profile_examples``.

    Each entry names the file and line of a ``max_examples=`` keyword whose
    value is not a call of ``profile_examples``, in the test infrastructure
    package or in a Python file under the Product Tree.
    """

    unrouted: list[str] = []
    for tree_root in EXAMPLE_COUNT_ROOTS:
        for path in sorted((root / tree_root).rglob(f"*{PYTHON_SUFFIX}")):
            if path.relative_to(root).as_posix() == PROFILE_REGISTRY_PATH:
                continue
            source = path.read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(source, filename=str(path))):
                if not isinstance(node, ast.Call):
                    continue
                for keyword in node.keywords:
                    if keyword.arg == MAX_EXAMPLES_KEYWORD and not _routed(
                        keyword.value
                    ):
                        unrouted.append(
                            f"{path.relative_to(root).as_posix()}:{keyword.value.lineno}"
                        )
    return tuple(unrouted)


def _routed(value: ast.expr) -> bool:
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == PROFILE_EXAMPLES_FUNCTION
    )

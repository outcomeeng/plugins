"""Whole-payload pytest module run inside a scratch worktree.

It holds a passing test, a failing test, and a closing test, run in that order.
Each creates temp files through ``tempfile``, ``tmp_path``, and a child process,
and records what it observed in the report file the harness names. It states no
expectation about those observations.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from outcomeeng_testing.harnesses.run_temp_root import (
    GIT_CEILING_VARIABLE,
    RUN_ROOTS_RELATIVE,
    TEMP_VARIABLE,
)
from outcomeeng_testing.harnesses.run_temp_root_observation import (
    CHANNEL_CHILD,
    CHANNEL_TEMPFILE,
    CHANNEL_TMP_PATH,
    FAILING_TEST,
    PASSING_TEST,
    REPORT_VARIABLE,
)

CHILD_SOURCE = "import tempfile; print(tempfile.mkstemp()[1])"
GIT_PROBE = ("git", "rev-parse", "--is-inside-work-tree")


def _record(**facts: object) -> None:
    report = Path(os.environ[REPORT_VARIABLE])
    data = json.loads(report.read_text()) if report.exists() else {}
    data.update(facts)
    report.write_text(json.dumps(data))


def _create_temp_files(tmp_path: Path) -> dict[str, str]:
    descriptor, through_tempfile = tempfile.mkstemp()
    os.close(descriptor)
    through_tmp_path = tmp_path / "created.txt"
    through_tmp_path.write_text("created")
    child = subprocess.run(
        [sys.executable, "-c", CHILD_SOURCE],
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        CHANNEL_TEMPFILE: through_tempfile,
        CHANNEL_TMP_PATH: str(through_tmp_path),
        CHANNEL_CHILD: child.stdout.strip(),
    }


def test_passing(tmp_path: Path) -> None:
    created = _create_temp_files(tmp_path)
    probe_directory = tempfile.mkdtemp()
    git = subprocess.run(GIT_PROBE, cwd=probe_directory, capture_output=True, text=True)
    roots = Path.cwd() / RUN_ROOTS_RELATIVE
    _record(
        first_test={
            "temp_variable": os.environ[TEMP_VARIABLE],
            "default_tempdir": tempfile.gettempdir(),
            "git_ceiling": os.environ.get(GIT_CEILING_VARIABLE),
            "run_roots_present": sorted(entry.name for entry in roots.iterdir()),
            "git_probe_returncode": git.returncode,
        },
        created=created,
        tmp_paths={PASSING_TEST: created[CHANNEL_TMP_PATH]},
    )


def test_failing(tmp_path: Path) -> None:
    created = _create_temp_files(tmp_path)
    report = json.loads(Path(os.environ[REPORT_VARIABLE]).read_text())
    _record(tmp_paths={**report["tmp_paths"], FAILING_TEST: created[CHANNEL_TMP_PATH]})
    raise AssertionError("failing test of the scratch run")


def test_closing() -> None:
    report = json.loads(Path(os.environ[REPORT_VARIABLE]).read_text())
    _record(
        retained={
            name: Path(path).exists() for name, path in report["tmp_paths"].items()
        }
    )

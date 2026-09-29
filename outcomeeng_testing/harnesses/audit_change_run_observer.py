"""Process observer for one audit-change runner invocation.

The audit-change harness starts this script in place of the runner:

    python3 audit_change_run_observer.py <runner-script> <report-path> [--race <candidate>]

It installs an audit hook that records every filesystem mutation the process
performs and every process it starts, wherever the path lies, then runs the
runner in this process with the caller's stdin and stdout. On exit it stops
recording and writes the record to ``<report-path>`` as one JSON object with
``writes`` and ``spawns``. The observation covers the runner process itself;
what a started process writes is outside it, and ``spawns`` names every such
process.

With ``--race``, the runner's entry point receives a command collaborator
that delegates every command to the runner's own subprocess adapter and, just
before the first ``spx`` command, appends to ``<candidate>`` as another agent
session editing it would. That is ``/test`` Stage 5 exception 3, time and
concurrency: no real session can be scheduled into the interval between the
runner's read of the candidate and SPX's retention of it. The observer stops
recording around its own edit, so the record holds only the runner's writes.

The observer decides nothing; the linked test owns every predicate.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import runpy
import sys
from collections.abc import Sequence
from types import ModuleType
from typing import Final

#: Report key for the filesystem mutations the runner process performed.
WRITES: Final = "writes"
#: Report key for the argument vectors of the processes the runner started.
SPAWNS: Final = "spawns"
#: Option naming the candidate the observer edits before the first SPX command.
RACE_OPTION: Final = "--race"
#: Text the observer appends to a candidate, as another session's edit would.
CANDIDATE_EDIT: Final = "\n"

_OPEN_EVENT: Final = "open"
_POPEN_EVENT: Final = "subprocess.Popen"
_WRITE_FLAGS: Final = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
_MUTATION_EVENTS: Final = frozenset(
    {
        "os.chmod",
        "os.chown",
        "os.link",
        "os.mkdir",
        "os.mkfifo",
        "os.mknod",
        "os.remove",
        "os.rename",
        "os.rmdir",
        "os.symlink",
        "os.truncate",
        "os.utime",
        "shutil.copyfile",
        "shutil.copytree",
        "shutil.move",
        "shutil.rmtree",
        "tempfile.mkdtemp",
        "tempfile.mkstemp",
    }
)
_OTHER_SPAWN_EVENTS: Final = frozenset(
    {"os.exec", "os.fork", "os.forkpty", "os.posix_spawn", "os.spawn", "os.system"}
)
_RUNNER_MODULE_NAME: Final = "audit_change_run"


class _Recorder:
    """Audit hook that records mutations and process starts while enabled."""

    def __init__(self) -> None:
        self.recording = True
        self.writes: list[list[str]] = []
        self.spawns: list[list[str]] = []

    def __call__(self, event: str, args: tuple[object, ...]) -> None:
        if not self.recording:
            return
        if event == _OPEN_EVENT:
            # An integer names a descriptor that is already open, such as the
            # pipe carrying a started process's stdin; it creates no file.
            if isinstance(args[0], int):
                return
            flags = args[2] if len(args) > 2 else None
            if isinstance(flags, int) and flags & _WRITE_FLAGS:
                self.writes.append([event, str(args[0])])
        elif event in _MUTATION_EVENTS:
            self.writes.append([event, *(str(arg) for arg in args[:1])])
        elif event == _POPEN_EVENT:
            argv = args[1] if len(args) > 1 else ()
            self.spawns.append(
                [str(arg) for arg in argv]
                if isinstance(argv, list | tuple)
                else [str(argv)]
            )
        elif event in _OTHER_SPAWN_EVENTS:
            self.spawns.append([event, *(str(arg) for arg in args[:2])])


def _load_runner(runner_script: pathlib.Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(_RUNNER_MODULE_NAME, runner_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the audit-change runner from {runner_script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_RUNNER_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _run_entry_point(runner_script: pathlib.Path) -> int:
    try:
        runpy.run_path(str(runner_script), run_name="__main__")
    except SystemExit as exit_request:
        code = exit_request.code
        return code if isinstance(code, int) else 1
    return 0


def _run_racing_entry_point(
    runner_script: pathlib.Path, candidate: str, recorder: _Recorder
) -> int:
    runner = _load_runner(runner_script)
    edited = False

    def racing(
        argv: Sequence[str], /, *, cwd: pathlib.Path, stdin: str | None
    ) -> object:
        nonlocal edited
        if argv[0] == runner.SPX_EXECUTABLE and not edited:
            recorder.recording = False
            try:
                with (cwd / candidate).open("a", encoding="utf-8") as handle:
                    handle.write(CANDIDATE_EDIT)
            finally:
                recorder.recording = True
            edited = True
        return runner.run_subprocess(argv, cwd=cwd, stdin=stdin)

    return int(runner.main(runner=racing))


def main(arguments: Sequence[str]) -> int:
    """Run the runner under observation and write the record to the report path."""
    runner_script = pathlib.Path(arguments[0])
    report = pathlib.Path(arguments[1])
    race = arguments[3] if list(arguments[2:3]) == [RACE_OPTION] else None
    sys.dont_write_bytecode = True
    recorder = _Recorder()
    sys.addaudithook(recorder)
    try:
        if race is None:
            return _run_entry_point(runner_script)
        return _run_racing_entry_point(runner_script, race, recorder)
    finally:
        recorder.recording = False
        report.write_text(
            json.dumps({WRITES: recorder.writes, SPAWNS: recorder.spawns}),
            encoding="utf-8",
        )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

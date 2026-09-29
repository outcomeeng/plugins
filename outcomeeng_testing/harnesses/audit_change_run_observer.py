"""Process observer for audit-change runner invocations.

The audit-change harness starts this script in place of the runner:

    python3 audit_change_run_observer.py <runner-script> <report-path>

It installs an audit hook that records every filesystem mutation the process
performs and every process it starts, wherever the path lies, then runs the
runner in this process with the caller's stdin and stdout. On exit it stops
recording and writes the record to ``<report-path>`` as one JSON object with
``writes`` and ``spawns``. The observation covers the runner process itself;
what a started process writes is outside it, and ``spawns`` names every such
process.

The harness also installs one ``Recorder`` in its own process to observe the
runner's entry point called in that process; a recorder started for one
thread records only that thread's events.

The observer decides nothing; the linked test owns every predicate.
"""

from __future__ import annotations

import json
import os
import pathlib
import runpy
import sys
import threading
from collections.abc import Sequence
from typing import Final

#: Report key for the filesystem mutations the runner process performed.
WRITES: Final = "writes"
#: Report key for the argument vectors of the processes the runner started.
SPAWNS: Final = "spawns"

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


class Recorder:
    """Audit hook that records mutations and process starts between start and stop.

    ``start`` clears the record; with ``thread`` it records only the events of
    that thread, otherwise the events of every thread. ``stop`` ends recording
    and returns the writes and spawns recorded since ``start``.
    """

    def __init__(self) -> None:
        self._recording = False
        self._thread: int | None = None
        self._writes: list[list[str]] = []
        self._spawns: list[list[str]] = []

    def start(self, *, thread: int | None = None) -> None:
        """Clear the record and begin recording."""
        self._writes = []
        self._spawns = []
        self._thread = thread
        self._recording = True

    def stop(self) -> tuple[list[list[str]], list[list[str]]]:
        """End recording and return ``(writes, spawns)``."""
        self._recording = False
        return self._writes, self._spawns

    def __call__(self, event: str, args: tuple[object, ...]) -> None:
        if not self._recording:
            return
        if self._thread is not None and threading.get_ident() != self._thread:
            return
        if event == _OPEN_EVENT:
            path = args[0]
            # An integer names a descriptor that is already open, such as the
            # pipe carrying a started process's stdin; it creates no file.
            if isinstance(path, int):
                return
            # ``subprocess`` opens the null device read-write to give a started
            # process an empty stdin; the device holds no content.
            if str(path) == os.devnull:
                return
            flags = args[2] if len(args) > 2 else None
            if isinstance(flags, int) and flags & _WRITE_FLAGS:
                self._writes.append([event, str(path)])
        elif event in _MUTATION_EVENTS:
            self._writes.append([event, *(str(arg) for arg in args[:1])])
        elif event == _POPEN_EVENT:
            argv = args[1] if len(args) > 1 else ()
            self._spawns.append(
                [str(arg) for arg in argv]
                if isinstance(argv, list | tuple)
                else [str(argv)]
            )
        elif event in _OTHER_SPAWN_EVENTS:
            self._spawns.append([event, *(str(arg) for arg in args[:2])])


def _run_entry_point(runner_script: pathlib.Path) -> int:
    try:
        runpy.run_path(str(runner_script), run_name="__main__")
    except SystemExit as exit_request:
        code = exit_request.code
        return code if isinstance(code, int) else 1
    return 0


def main(arguments: Sequence[str]) -> int:
    """Run the runner under observation and write the record to the report path."""
    runner_script = pathlib.Path(arguments[0])
    report = pathlib.Path(arguments[1])
    sys.dont_write_bytecode = True
    recorder = Recorder()
    sys.addaudithook(recorder)
    recorder.start()
    try:
        return _run_entry_point(runner_script)
    finally:
        writes, spawns = recorder.stop()
        report.write_text(
            json.dumps({WRITES: writes, SPAWNS: spawns}),
            encoding="utf-8",
        )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

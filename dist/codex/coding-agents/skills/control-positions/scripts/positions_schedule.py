#!/usr/bin/env python3
"""Management of the macOS launchd job that starts one finite pass per interval."""

from __future__ import annotations

import os
import plistlib
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Protocol

JOB_LABEL: Final = "engineering.outcome.usage-control.positions"
PASS_INTERVAL_MINUTES: Final = 30
SECONDS_PER_MINUTE: Final = 60
DARWIN_PLATFORM: Final = "darwin"
LAUNCHCTL: Final = "/bin/launchctl"
ENTRY_POINT_NAME: Final = "control_positions.py"
ABSENT_SERVICE_TEXT: Final = "could not find service"
PLIST_SUFFIX: Final = ".plist"
REPORTS_FILE_NAME: Final = "scheduled-pass-reports.log"
ERRORS_FILE_NAME: Final = "scheduled-pass-errors.log"


class ScheduleOperation(StrEnum):
    INSTALL = "install"
    STATUS = "status"
    STOP = "stop"
    RESTART = "restart"


class ScheduleStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ScheduleResult:
    status: ScheduleStatus
    detail: str


class CommandOutcome(Protocol):
    @property
    def returncode(self) -> int: ...

    @property
    def stdout(self) -> str: ...

    @property
    def stderr(self) -> str: ...


class CommandRunner(Protocol):
    def run(
        self, argv: tuple[str, ...], stdin: str | None = None
    ) -> CommandOutcome: ...


def _outcome_result(outcome: CommandOutcome, success: str) -> ScheduleResult:
    if outcome.returncode == 0:
        return ScheduleResult(
            ScheduleStatus.SUCCEEDED, outcome.stdout.strip() or success
        )
    detail = outcome.stderr.strip() or outcome.stdout.strip() or "no command detail"
    return ScheduleResult(ScheduleStatus.FAILED, detail)


def _owned(path: Path) -> bool:
    """Whether the file at `path` is a plist an install of this controller wrote.

    Owned means an existing regular file that parses as a plist whose Label equals the
    job label and whose ProgramArguments name this controller's pass entry point.
    """
    if path.is_symlink() or not path.is_file():
        return False
    try:
        document = plistlib.loads(path.read_bytes())
    except (OSError, plistlib.InvalidFileException, ValueError):
        return False
    if not isinstance(document, dict) or document.get("Label") != JOB_LABEL:
        return False
    arguments = document.get("ProgramArguments")
    return isinstance(arguments, list) and any(
        isinstance(item, str) and Path(item).name == ENTRY_POINT_NAME
        for item in arguments
    )


def _write(path: Path, content: bytes) -> None:
    """Publish `content` at `path` through a unique temporary file, never a link."""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=".usage-control-positions-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _install(
    runner: CommandRunner,
    domain: str,
    launch_agents_dir: Path,
    program: Sequence[str],
    data_root: Path,
) -> ScheduleResult:
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents_dir / f"{JOB_LABEL}{PLIST_SUFFIX}"
    if plist_path.is_symlink() or (plist_path.exists() and not _owned(plist_path)):
        return ScheduleResult(
            ScheduleStatus.FAILED,
            f"Unowned launch agent exists: {plist_path}; inspect it before installation",
        )
    document = {
        "Label": JOB_LABEL,
        "ProgramArguments": list(program),
        "StartInterval": PASS_INTERVAL_MINUTES * SECONDS_PER_MINUTE,
        "RunAtLoad": False,
        "StandardOutPath": str(data_root / REPORTS_FILE_NAME),
        "StandardErrorPath": str(data_root / ERRORS_FILE_NAME),
    }
    try:
        _write(plist_path, plistlib.dumps(document))
    except OSError as error:
        return ScheduleResult(
            ScheduleStatus.FAILED, f"Cannot write {plist_path}: {error}"
        )
    target = f"{domain}/{JOB_LABEL}"
    state = runner.run((LAUNCHCTL, "print", target))
    if state.returncode == 0:
        unloaded = runner.run((LAUNCHCTL, "bootout", target))
        if unloaded.returncode != 0:
            return _outcome_result(unloaded, "")
    elif ABSENT_SERVICE_TEXT not in (state.stderr + state.stdout).lower():
        return _outcome_result(state, "")
    outcome = runner.run((LAUNCHCTL, "bootstrap", domain, str(plist_path)))
    return _outcome_result(outcome, f"installed {plist_path}")


def run_schedule(
    operation: ScheduleOperation,
    runner: CommandRunner,
    platform: str,
    launch_agents_dir: Path,
    program: Sequence[str],
    data_root: Path,
) -> ScheduleResult:
    """Run one scheduling operation; any platform but macOS reports unsupported."""
    if platform != DARWIN_PLATFORM:
        return ScheduleResult(
            ScheduleStatus.UNSUPPORTED,
            f"scheduling is supported on macOS only, not on {platform}",
        )
    domain = f"gui/{os.getuid()}"
    target = f"{domain}/{JOB_LABEL}"
    if operation is ScheduleOperation.INSTALL:
        return _install(runner, domain, launch_agents_dir, program, data_root)
    if operation is ScheduleOperation.STATUS:
        return _outcome_result(
            runner.run((LAUNCHCTL, "print", target)), "job is loaded"
        )
    if operation is ScheduleOperation.STOP:
        return _outcome_result(
            runner.run((LAUNCHCTL, "bootout", target)), "job stopped"
        )
    return _outcome_result(
        runner.run((LAUNCHCTL, "kickstart", "-k", target)), "job restarted"
    )

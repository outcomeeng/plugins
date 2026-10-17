#!/usr/bin/env python3
"""Management of the macOS launchd job that starts one finite pass per interval."""

from __future__ import annotations

import os
import plistlib
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Protocol

JOB_LABEL: Final = "engineering.outcome.usage-control.positions"
PASS_INTERVAL_MINUTES: Final = 30
SECONDS_PER_MINUTE: Final = 60
DARWIN_PLATFORM: Final = "darwin"
LAUNCHCTL: Final = "launchctl"
PLIST_SUFFIX: Final = ".plist"


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


def _install(
    runner: CommandRunner,
    domain: str,
    launch_agents_dir: Path,
    program: Sequence[str],
) -> ScheduleResult:
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents_dir / f"{JOB_LABEL}{PLIST_SUFFIX}"
    document = {
        "Label": JOB_LABEL,
        "ProgramArguments": list(program),
        "StartInterval": PASS_INTERVAL_MINUTES * SECONDS_PER_MINUTE,
        "RunAtLoad": False,
    }
    plist_path.write_bytes(plistlib.dumps(document))
    runner.run((LAUNCHCTL, "bootout", f"{domain}/{JOB_LABEL}"))
    outcome = runner.run((LAUNCHCTL, "bootstrap", domain, str(plist_path)))
    return _outcome_result(outcome, f"installed {plist_path}")


def run_schedule(
    operation: ScheduleOperation,
    runner: CommandRunner,
    platform: str,
    launch_agents_dir: Path,
    program: Sequence[str],
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
        return _install(runner, domain, launch_agents_dir, program)
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

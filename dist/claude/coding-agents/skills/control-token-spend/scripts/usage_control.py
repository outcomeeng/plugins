"""Finite local usage collection, reporting, detection and scheduling operations."""

from __future__ import annotations

from enum import StrEnum

import argparse
import datetime as dt
import fcntl
import json
import os
import signal
import sqlite3
import sys
from pathlib import Path
from typing import TextIO

from usage_accounting import AccountingField
from usage_reports import ReportField, ALERT_DIRECTORY
from usage_schedule import ScheduleField
from usage_accounting import (
    DEFAULT_PROJECTS,
    DEFAULT_ROOT,
    HOUR,
    LOCK_NAME,
    QUARTER,
    RETENTION_DAYS,
    TOKEN_KEYS,
    UTC,
    Config,
    Evidence,
    Json,
    encoded,
    iso,
    signals,
    timestamp,
)
from usage_reports import behavior, json_write, retain_alerts, write_report
from usage_schedule import (
    CONFIG_NAME,
    Runner,
    SubprocessRunner,
    install,
    investigate,
    jobs,
)

OPERATIONS = (
    "collect",
    "report",
    "detect",
    "hourly",
    "install",
    "status",
    "stop",
    "restart",
)
MAX_WORKER_SECONDS = 120
MAX_LOG_BYTES = 64 * 1024
FAILURE_EXIT = 1
SUCCESS_EXIT = 0
OVERLAP_STATUS = "overlap_skipped"
ALREADY_RECORDED_STATUS = "already_recorded"


class Option(StrEnum):
    ROOT = "--root"
    PROJECTS = "--projects"
    START = "--start"
    END = "--end"
    ACTIVATE = "--activate"
    LAUNCH_AGENTS_DIR = "--launch-agents-dir"
    AISE = "--aise"
    AISE_DATABASE = "--aise-database"


class ControlField(StrEnum):
    """Wire fields consumed by the module's public evidence contract."""

    ARTIFACT = "artifact"
    INVESTIGATION = "investigation"
    SIGNALS = "signals"


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Bounded local usage evidence and advisory spending signals."
    )
    value.add_argument("operation", choices=OPERATIONS, nargs="?", default="report")
    value.add_argument(
        Option.ROOT,
        type=Path,
        default=DEFAULT_ROOT,
        help="Stable operator-owned state and artifact root",
    )
    value.add_argument(
        Option.PROJECTS,
        type=Path,
        help="Read-only transcript root; defaults to the saved installation or ~/.claude/projects",
    )
    value.add_argument(Option.START, help="Inclusive ISO 8601 measurement start")
    value.add_argument(
        Option.END, help="Exclusive ISO 8601 measurement end; defaults to now"
    )
    value.add_argument(
        Option.ACTIVATE,
        action="store_true",
        help="Explicitly install and activate launchd jobs; install otherwise returns a plan",
    )
    value.add_argument(
        Option.LAUNCH_AGENTS_DIR,
        type=Path,
        default=Path.home() / "Library/LaunchAgents",
    )
    value.add_argument(
        Option.AISE,
        type=Path,
        help="Explicit optional supported existing-index query executable",
    )
    value.add_argument(
        Option.AISE_DATABASE,
        type=Path,
        help="Explicit existing investigation index; never built or refreshed here",
    )
    return value


def configuration(args: argparse.Namespace, end: dt.datetime) -> Config:
    environment: dict[str, str] = {}
    root = args.root.expanduser().resolve()
    saved = root / CONFIG_NAME
    saved_projects = DEFAULT_PROJECTS
    if saved.exists():
        if saved.is_symlink() or saved.stat().st_size > MAX_LOG_BYTES:
            raise ValueError(
                f"Invalid saved configuration file: {saved}; inspect its path and size"
            )
        value = json.loads(saved.read_text())
        if not isinstance(value, dict):
            raise ValueError(f"Saved configuration must be a JSON object: {saved}")
        environment.update(
            {
                key: str(item)
                for key, item in value.items()
                if key.startswith("SPX_USAGE_") and item is not None
            }
        )
        saved_projects = Path(value.get("projects", str(DEFAULT_PROJECTS)))
    environment.update(os.environ)
    config = Config.from_environment(environment, root, args.projects or saved_projects)
    config.period(end)
    return config


def timeout(_signum: int, _frame: object) -> None:
    raise TimeoutError(
        f"Worker exceeded its {MAX_WORKER_SECONDS}-second limit; inspect status and resume with the same state root"
    )


def rotate_logs(root: Path) -> None:
    for name in (
        "detect.stdout.log",
        "detect.stderr.log",
        "hourly.stdout.log",
        "hourly.stderr.log",
    ):
        path = root / name
        if path.is_symlink():
            raise ValueError(
                f"Managed log is symlinked: {path}; inspect it before running a worker"
            )
        if not path.exists() or path.stat().st_size <= MAX_LOG_BYTES:
            continue
        with path.open("r+b") as stream:
            stream.seek(-MAX_LOG_BYTES, os.SEEK_END)
            content = stream.read(MAX_LOG_BYTES)
            stream.seek(0)
            stream.write(content)
            stream.truncate()
            own_inode = os.fstat(stream.fileno())
            for descriptor in (1, 2):
                try:
                    inherited = os.fstat(descriptor)
                    if (inherited.st_dev, inherited.st_ino) == (
                        own_inode.st_dev,
                        own_inode.st_ino,
                    ):
                        os.lseek(descriptor, 0, os.SEEK_END)
                except OSError:
                    # A pipe or closed inherited descriptor has no managed-file offset.
                    continue


def worker(
    args: argparse.Namespace, config: Config, end: dt.datetime, runner: Runner
) -> Json:
    with Evidence(config) as evidence:
        collection = evidence.collect(end)
        retention_gaps = retain_alerts(
            config.root, iso(end - dt.timedelta(days=RETENTION_DAYS))
        )
        if retention_gaps:
            collection[AccountingField.GAPS].extend(retention_gaps)
            collection["history_complete"] = False
            with evidence.db:
                evidence.set_setting("collection", encoded(collection))
        if args.operation == "collect":
            return {
                ScheduleField.STATUS: "collected",
                "collection": collection,
                AccountingField.CONFIGURATION: config.effective(),
                ReportField.MODEL_INVOCATIONS: 0,
            }
        if args.operation == "detect":
            current = evidence.measure(end - QUARTER, end)
            week_start, _ = config.period(end)
            weekly: Json = (
                evidence.measure(week_start, end)
                if week_start < end
                else {
                    AccountingField.API_EQUIVALENT_USD: 0,
                    AccountingField.START_UTC: iso(end),
                    AccountingField.END_EXCLUSIVE_UTC: iso(end),
                    AccountingField.GAPS: [],
                }
            )
            emitted = []
            for value in signals(config, current, weekly, end):
                identity = value[AccountingField.IDENTITY]
                value["evidence"] = str(
                    config.root / ALERT_DIRECTORY / (identity + ".json")
                )
                with evidence.db:
                    prior = evidence.db.execute(
                        "SELECT payload FROM signals WHERE identity=?", (identity,)
                    ).fetchone()
                    if prior:
                        emitted.append(
                            {
                                AccountingField.IDENTITY: identity,
                                ScheduleField.STATUS: ALREADY_RECORDED_STATUS,
                                "evidence": value["evidence"],
                            }
                        )
                        continue
                    json_write(
                        Path(value["evidence"]),
                        {"signal": value, "current": current, "weekly": weekly},
                    )
                    evidence.db.execute(
                        "INSERT INTO signals VALUES(?,?,?)",
                        (identity, encoded(value), iso(end)),
                    )
                emitted.append(
                    {
                        AccountingField.IDENTITY: identity,
                        ScheduleField.STATUS: "recorded",
                        "evidence": value["evidence"],
                    }
                )
            return {
                ScheduleField.STATUS: "signals_recorded"
                if emitted
                else "coverage_incomplete"
                if current[AccountingField.GAPS] or weekly[AccountingField.GAPS]
                else "below_measured_thresholds",
                ControlField.SIGNALS: emitted,
                AccountingField.START_UTC: current[AccountingField.START_UTC],
                AccountingField.END_EXCLUSIVE_UTC: current[
                    AccountingField.END_EXCLUSIVE_UTC
                ],
                AccountingField.API_EQUIVALENT_USD: current[
                    AccountingField.API_EQUIVALENT_USD
                ],
                "weekly_api_equivalent_usd": weekly[AccountingField.API_EQUIVALENT_USD],
                AccountingField.CONFIGURATION: config.effective(),
                AccountingField.GAPS: sorted(
                    set(current[AccountingField.GAPS] + weekly[AccountingField.GAPS])
                ),
                ReportField.MODEL_INVOCATIONS: 0,
                AccountingField.SUBSCRIPTION_USAGE_CONVERSION: None,
            }
        report_end = (
            end.replace(minute=0, second=0, microsecond=0)
            if args.operation == "hourly"
            else end
        )
        start = timestamp(args.start, Option.START) if args.start else report_end - HOUR
        current = evidence.measure(start, report_end)
        previous = evidence.measure(start - (report_end - start), start)
        screening = behavior(evidence, current)
        investigation = investigate(runner, args.aise, args.aise_database, current)
        current[ControlField.INVESTIGATION] = investigation
        path = write_report(config.root, current, screening, previous)
        return {
            ScheduleField.STATUS: "report_created",
            ControlField.ARTIFACT: str(path),
            AccountingField.START_UTC: current[AccountingField.START_UTC],
            AccountingField.END_EXCLUSIVE_UTC: current[
                AccountingField.END_EXCLUSIVE_UTC
            ],
            AccountingField.REQUESTS: current[AccountingField.REQUESTS],
            AccountingField.USAGE: {key: current[key] for key in TOKEN_KEYS},
            AccountingField.API_EQUIVALENT_USD: current[
                AccountingField.API_EQUIVALENT_USD
            ],
            AccountingField.GAPS: current[AccountingField.GAPS],
            AccountingField.CONFIGURATION: config.effective(),
            ReportField.MODEL_INVOCATIONS: 0,
        }


def execute(
    args: argparse.Namespace, output: TextIO, runner: Runner | None = None
) -> int:
    runner = runner if runner is not None else SubprocessRunner()
    root = args.root.expanduser().resolve()
    if args.activate and args.operation != "install":
        raise ValueError(
            "--activate: valid only for install; choose install to activate scheduling"
        )
    if args.operation in ("status", "stop", "restart"):
        if args.operation != "status" and root.exists():
            if (root / LOCK_NAME).is_symlink():
                raise ValueError(f"Worker lock is symlinked: {root / LOCK_NAME}")
            with (root / LOCK_NAME).open("a+") as lock:
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    print(
                        json.dumps(
                            {
                                ScheduleField.STATUS: OVERLAP_STATUS,
                                "operation": args.operation,
                                "root": str(root),
                            }
                        ),
                        file=output,
                    )
                    return SUCCESS_EXIT
                result = jobs(root, args.operation, runner, sys.platform)
        else:
            result = jobs(root, args.operation, runner, sys.platform)
        status = root / "worker-status.json"
        if (
            status.exists()
            and not status.is_symlink()
            and status.stat().st_size <= MAX_LOG_BYTES
        ):
            result["last_worker"] = json.loads(status.read_text())
        else:
            result["last_worker_gap"] = (
                "Worker status is absent, symlinked or exceeds the inspection bound."
            )
        print(json.dumps(result), file=output)
        return (
            SUCCESS_EXIT
            if result[ScheduleField.STATUS]
            in ("inspected", "completed", "not_installed")
            else FAILURE_EXIT
        )
    end = timestamp(args.end, Option.END) if args.end else dt.datetime.now(UTC)
    config = configuration(args, end)
    effective_end = (
        end.replace(minute=0, second=0, microsecond=0)
        if args.operation == "hourly"
        else end
    )
    if args.start and timestamp(args.start, Option.START) >= effective_end:
        raise ValueError("measurement window: --start must precede --end")
    if (args.aise is None) != (args.aise_database is None):
        raise ValueError("investigation: supply both --aise and --aise-database")
    root.mkdir(parents=True, exist_ok=True)
    if (root / LOCK_NAME).is_symlink():
        raise ValueError(
            f"Worker lock is symlinked: {root / LOCK_NAME}; inspect its ownership"
        )
    with (root / LOCK_NAME).open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(
                json.dumps(
                    {
                        ScheduleField.STATUS: OVERLAP_STATUS,
                        "root": str(root),
                        ReportField.MODEL_INVOCATIONS: 0,
                    }
                ),
                file=output,
            )
            return SUCCESS_EXIT
        prior_handler = signal.signal(signal.SIGALRM, timeout)
        signal.alarm(MAX_WORKER_SECONDS)
        try:
            if args.operation == "install":
                result = install(
                    config,
                    Path(__file__).resolve().parent,
                    args.launch_agents_dir.expanduser().resolve(),
                    runner,
                    sys.platform,
                    args.activate,
                )
            else:
                rotate_logs(root)
                result = worker(args, config, end, runner)
            result["generated_at_utc"] = iso(dt.datetime.now(UTC))
            json_write(root / "worker-status.json", result)
            print(json.dumps(result), file=output)
            return (
                FAILURE_EXIT
                if result[ScheduleField.STATUS] in ("failed", "unsupported")
                else SUCCESS_EXIT
            )
        except (
            OSError,
            ValueError,
            RuntimeError,
            TimeoutError,
            sqlite3.Error,
        ) as error:
            result = {
                ScheduleField.STATUS: "failed",
                "operation": args.operation,
                "error": str(error),
                "generated_at_utc": iso(dt.datetime.now(UTC)),
                "root": str(root),
            }
            json_write(root / "worker-status.json", result)
            raise
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, prior_handler)


def main() -> int:
    args = parser().parse_args()
    try:
        return execute(args, sys.stdout)
    except (OSError, ValueError, RuntimeError, TimeoutError, sqlite3.Error) as error:
        print(
            json.dumps(
                {
                    ScheduleField.STATUS: "failed",
                    "operation": args.operation,
                    "error": str(error),
                }
            ),
            file=sys.stderr,
        )
        return FAILURE_EXIT


if __name__ == "__main__":
    raise SystemExit(main())

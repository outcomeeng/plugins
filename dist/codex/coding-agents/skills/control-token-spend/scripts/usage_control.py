"""Finite local usage collection, reporting, detection and scheduling operations."""

from __future__ import annotations

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


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Bounded local usage evidence and advisory spending signals."
    )
    value.add_argument("operation", choices=OPERATIONS, nargs="?", default="report")
    value.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Stable operator-owned state and artifact root",
    )
    value.add_argument(
        "--projects",
        type=Path,
        help="Read-only transcript root; defaults to the saved installation or ~/.claude/projects",
    )
    value.add_argument("--start", help="Inclusive ISO 8601 measurement start")
    value.add_argument(
        "--end", help="Exclusive ISO 8601 measurement end; defaults to now"
    )
    value.add_argument(
        "--activate",
        action="store_true",
        help="Explicitly install and activate launchd jobs; install otherwise returns a plan",
    )
    value.add_argument(
        "--launch-agents-dir", type=Path, default=Path.home() / "Library/LaunchAgents"
    )
    value.add_argument(
        "--aise",
        type=Path,
        help="Explicit optional supported existing-index query executable",
    )
    value.add_argument(
        "--aise-database",
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
            collection["gaps"].extend(retention_gaps)
            collection["history_complete"] = False
            with evidence.db:
                evidence.set_setting("collection", encoded(collection))
        if args.operation == "collect":
            return {
                "status": "collected",
                "collection": collection,
                "configuration": config.effective(),
                "model_invocations": 0,
            }
        if args.operation == "detect":
            current = evidence.measure(end - QUARTER, end)
            week_start, _ = config.period(end)
            weekly = (
                evidence.measure(week_start, end)
                if week_start < end
                else {
                    "api_equivalent_usd": 0,
                    "start_utc": iso(end),
                    "end_exclusive_utc": iso(end),
                    "gaps": [],
                }
            )
            emitted = []
            for value in signals(config, current, weekly, end):
                identity = value["identity"]
                value["evidence"] = str(config.root / "alerts" / (identity + ".json"))
                with evidence.db:
                    prior = evidence.db.execute(
                        "SELECT payload FROM signals WHERE identity=?", (identity,)
                    ).fetchone()
                    if prior:
                        emitted.append(
                            {
                                "identity": identity,
                                "status": ALREADY_RECORDED_STATUS,
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
                        "identity": identity,
                        "status": "recorded",
                        "evidence": value["evidence"],
                    }
                )
            return {
                "status": "signals_recorded"
                if emitted
                else "coverage_incomplete"
                if current["gaps"] or weekly["gaps"]
                else "below_measured_thresholds",
                "signals": emitted,
                "start_utc": current["start_utc"],
                "end_exclusive_utc": current["end_exclusive_utc"],
                "api_equivalent_usd": current["api_equivalent_usd"],
                "weekly_api_equivalent_usd": weekly["api_equivalent_usd"],
                "configuration": config.effective(),
                "gaps": sorted(set(current["gaps"] + weekly["gaps"])),
                "model_invocations": 0,
                "subscription_usage_conversion": None,
            }
        report_end = (
            end.replace(minute=0, second=0, microsecond=0)
            if args.operation == "hourly"
            else end
        )
        start = timestamp(args.start, "--start") if args.start else report_end - HOUR
        current = evidence.measure(start, report_end)
        previous = evidence.measure(start - (report_end - start), start)
        screening = behavior(evidence, current)
        investigation = investigate(runner, args.aise, args.aise_database, current)
        current["investigation"] = investigation
        path = write_report(config.root, current, screening, previous)
        return {
            "status": "report_created",
            "artifact": str(path),
            "start_utc": current["start_utc"],
            "end_exclusive_utc": current["end_exclusive_utc"],
            "requests": current["requests"],
            "usage": {key: current[key] for key in TOKEN_KEYS},
            "api_equivalent_usd": current["api_equivalent_usd"],
            "gaps": current["gaps"],
            "configuration": config.effective(),
            "model_invocations": 0,
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
                                "status": OVERLAP_STATUS,
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
            if result["status"] in ("inspected", "completed", "not_installed")
            else FAILURE_EXIT
        )
    end = timestamp(args.end, "--end") if args.end else dt.datetime.now(UTC)
    config = configuration(args, end)
    effective_end = (
        end.replace(minute=0, second=0, microsecond=0)
        if args.operation == "hourly"
        else end
    )
    if args.start and timestamp(args.start, "--start") >= effective_end:
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
                        "status": OVERLAP_STATUS,
                        "root": str(root),
                        "model_invocations": 0,
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
                if result["status"] in ("failed", "unsupported")
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
                "status": "failed",
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
                {"status": "failed", "operation": args.operation, "error": str(error)}
            ),
            file=sys.stderr,
        )
        return FAILURE_EXIT


if __name__ == "__main__":
    raise SystemExit(main())

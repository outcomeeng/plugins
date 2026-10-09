"""Finite external operations, existing-index queries and managed launchd assets."""

from __future__ import annotations


import hashlib
import json
import os
import plistlib
import selectors
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum, StrEnum
from pathlib import Path
from typing import Protocol

from usage_accounting import AccountingField
from usage_accounting import Config, Json
from usage_reports import atomic_write, json_write

LABEL_PREFIX = "engineering.outcome.usage-control"
COMMAND_SECONDS = 30
COMMAND_BYTES = 64 * 1024
AISE_VERSION = "aise 1.0.0-rc.4"
AISE_SOURCE = "https://github.com/ahundt/ai-session-search"
SCRIPT_NAMES = (
    "usage_control.py",
    "usage_accounting.py",
    "usage_reports.py",
    "usage_schedule.py",
)
INSTALL_NAME = "installation.json"
CONFIG_NAME = "configuration.json"
AISE_QUERY_PREFIX = (
    "--index-refresh",
    "existing-only",
    "--skip-release-notification",
    "--threads",
    "1",
    "messages",
    "search",
    "error|failed|timeout|retry|rejected",
    "--query-mode",
    "regex",
    "--provider",
    "claude",
)
AISE_QUERY_SUFFIX = (
    "--limit",
    "12",
    "--context",
    "0",
    "--lines-per-message",
    "5",
    "--field-view-chars",
    "1000",
    "--format",
    "json",
)
AISE_START_OPTION = "--since"
AISE_END_OPTION = "--until"
AISE_DATABASE_OPTION = "--database"
AISE_VERSION_OPTION = "--version"

SUPPORTED_PYTHON = ((3, 13), (3, 14))
MODES = ("detect", "hourly")


LAUNCHCTL = "/bin/launchctl"


class LaunchctlOperation(StrEnum):
    BOOTSTRAP = "bootstrap"
    BOOTOUT = "bootout"
    PRINT = "print"


class JobOperation(StrEnum):
    STATUS = "status"
    STOP = "stop"
    RESTART = "restart"


class ScheduleField(StrEnum):
    """Wire fields consumed by the module's public evidence contract."""

    PROGRAMARGUMENTS = "ProgramArguments"
    ASSETS = "assets"
    JOBS = "jobs"
    LOADED = "loaded"
    PLIST = "plist"
    STATUS = "status"


class JobStatus(str, Enum):
    UNSUPPORTED = "unsupported"
    NOT_INSTALLED = "not_installed"
    INSPECTED = "inspected"
    COMPLETED = "completed"
    FAILED = "failed"


class InvestigationStatus(str, Enum):
    NOT_SELECTED = "not_selected"
    UNAVAILABLE = "unavailable"
    INCOMPATIBLE = "incompatible"
    QUERIED = "queried"
    FAILED = "failed"


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class Runner(Protocol):
    def run(
        self, argv: tuple[str, ...], timeout: int = COMMAND_SECONDS
    ) -> CommandResult: ...


class SubprocessRunner:
    def run(
        self, argv: tuple[str, ...], timeout: int = COMMAND_SECONDS
    ) -> CommandResult:
        captured: dict[str, bytearray] = {"stdout": bytearray(), "stderr": bytearray()}
        deadline = time.monotonic() + timeout
        with subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as process:
            if process.stdout is None or process.stderr is None:
                raise RuntimeError("Command capture pipes unavailable")
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
                    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
                    while selector.get_map():
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError(
                                f"Command exceeded {timeout} seconds: {argv[0]}"
                            )
                        for key, _ in selector.select(min(remaining, 1)):
                            chunk = os.read(key.fd, 4096)
                            if not chunk:
                                selector.unregister(key.fileobj)
                                continue
                            captured[key.data].extend(chunk)
                            if sum(map(len, captured.values())) > COMMAND_BYTES:
                                raise RuntimeError(
                                    f"Command exceeded {COMMAND_BYTES} captured bytes: {argv[0]}"
                                )
                    try:
                        result = process.wait(
                            timeout=max(0.01, deadline - time.monotonic())
                        )
                    except subprocess.TimeoutExpired as error:
                        raise TimeoutError(
                            f"Command exceeded {timeout} seconds: {argv[0]}"
                        ) from error
            except BaseException:
                process.kill()
                process.wait()
                raise
        return CommandResult(
            argv,
            result,
            captured["stdout"].decode(errors="replace"),
            captured["stderr"].decode(errors="replace"),
        )


def checked(runner: Runner, argv: tuple[str, ...]) -> CommandResult:
    result = runner.run(argv)
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {argv[0]}: {result.stderr[:2000]}"
        )
    return result


def absent(result: CommandResult) -> bool:
    return result.returncode != 0 and "could not find service" in result.stderr.lower()


def manifest(root: Path) -> Json | None:
    path = root / INSTALL_NAME
    if not path.exists():
        return None
    if path.is_symlink() or path.stat().st_size > COMMAND_BYTES:
        raise ValueError(f"Invalid installation manifest path or size: {path}")
    value = json.loads(path.read_text())
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or value.get("root") != str(root)
    ):
        raise ValueError(f"Invalid managed installation identity: {path}")
    recorded_jobs = value.get(ScheduleField.JOBS)
    if not isinstance(recorded_jobs, list) or len(recorded_jobs) != len(MODES):
        raise ValueError(f"Invalid managed jobs: {path}")
    assets = root / "assets" / str(value.get("asset_version"))
    if (
        value.get(ScheduleField.ASSETS) != str(assets)
        or len(assets.name) != 64
        or any(c not in "0123456789abcdef" for c in assets.name)
    ):
        raise ValueError(f"Invalid managed asset version: {path}")
    labels = set()
    for job in recorded_jobs:
        if not isinstance(job, dict):
            raise ValueError(f"Invalid managed job record: {path}")
        label = job.get("label")
        if (
            label not in tuple(LABEL_PREFIX + "." + mode for mode in MODES)
            or label in labels
        ):
            raise ValueError(f"Invalid managed job label: {path}")
        labels.add(label)
        location = Path(str(job.get("path")))
        settings = job.get(ScheduleField.PLIST)
        if (
            not location.is_absolute()
            or location.name != label + ".plist"
            or location.is_symlink()
            or not isinstance(settings, dict)
        ):
            raise ValueError(
                f"Invalid managed launch-agent path or configuration: {path}"
            )
        expected = [
            value.get("python"),
            "-B",
            str(assets / "usage_control.py"),
            label.rsplit(".", 1)[-1],
            "--root",
            str(root),
        ]
        if (
            settings.get("Label") != label
            or settings.get(ScheduleField.PROGRAMARGUMENTS) != expected
            or settings.get("WorkingDirectory") != str(root)
        ):
            raise ValueError(f"Managed job does not match installed assets: {path}")
    return value


def investigate(
    runner: Runner, executable: Path | None, database: Path | None, measurement: Json
) -> Json:
    if executable is None and database is None:
        return {
            ScheduleField.STATUS: InvestigationStatus.NOT_SELECTED,
            "gap": "Optional existing-index investigation was not selected.",
        }
    if executable is None or database is None:
        raise ValueError("investigation: supply both --aise and --aise-database")
    executable, database = (
        executable.expanduser().resolve(),
        database.expanduser().resolve(),
    )
    if not executable.is_file() or not database.is_file():
        return {
            ScheduleField.STATUS: InvestigationStatus.UNAVAILABLE,
            "gap": "Existing investigation executable or database is absent.",
            "executable": str(executable),
            "database": str(database),
        }
    try:
        version = checked(runner, (str(executable), AISE_VERSION_OPTION)).stdout.strip()
        if version != AISE_VERSION:
            return {
                ScheduleField.STATUS: InvestigationStatus.INCOMPATIBLE,
                "observed_version": version,
                "supported_version": AISE_VERSION,
                "gap": "Optional query skipped; the supported command contract differs.",
            }
        result = checked(
            runner,
            (
                str(executable),
                AISE_DATABASE_OPTION,
                str(database),
                *AISE_QUERY_PREFIX,
                AISE_START_OPTION,
                measurement[AccountingField.START_UTC],
                AISE_END_OPTION,
                measurement[AccountingField.END_EXCLUSIVE_UTC],
                *AISE_QUERY_SUFFIX,
            ),
        )
        return {
            ScheduleField.STATUS: InvestigationStatus.QUERIED,
            "version": version,
            "source": AISE_SOURCE,
            "database": str(database),
            "query_result": json.loads(result.stdout),
            "read_only_accounting": True,
            "gap": "Existing index coverage and timestamp boundary semantics remain independent of native accounting.",
        }
    except (
        OSError,
        RuntimeError,
        TimeoutError,
        ValueError,
        subprocess.TimeoutExpired,
    ) as error:
        return {
            ScheduleField.STATUS: InvestigationStatus.FAILED,
            "gap": f"Optional investigation failed; accounting preserved: {error}",
        }


def install_plan(
    config: Config, source: Path, python: Path, agents_directory: Path, platform: str
) -> Json:
    if platform != "darwin":
        return {
            ScheduleField.STATUS: "unsupported",
            "platform": platform,
            "gap": "Managed scheduling requires macOS launchd.",
        }
    payloads = {name: (source / name).read_bytes() for name in SCRIPT_NAMES}
    version = hashlib.sha256(
        b"".join(name.encode() + payloads[name] for name in SCRIPT_NAMES)
    ).hexdigest()
    assets = config.root / "assets" / version
    jobs = []
    for mode in MODES:
        label = LABEL_PREFIX + "." + mode
        schedule = (
            [{"Minute": minute} for minute in (0, 15, 30, 45)]
            if mode == "detect"
            else {"Minute": 0}
        )
        value = {
            "Label": label,
            ScheduleField.PROGRAMARGUMENTS: [
                str(python),
                "-B",
                str(assets / "usage_control.py"),
                mode,
                "--root",
                str(config.root),
            ],
            "StartCalendarInterval": schedule,
            "RunAtLoad": True,
            "ProcessType": "Background",
            "LowPriorityIO": True,
            "Nice": 10,
            "WorkingDirectory": str(config.root),
            "StandardOutPath": str(config.root / (mode + ".stdout.log")),
            "StandardErrorPath": str(config.root / (mode + ".stderr.log")),
        }
        jobs.append(
            {
                "label": label,
                "path": str(agents_directory / (label + ".plist")),
                ScheduleField.PLIST: value,
            }
        )
    return {
        "schema_version": 1,
        ScheduleField.STATUS: "planned",
        "asset_version": version,
        ScheduleField.ASSETS: str(assets),
        "root": str(config.root),
        AccountingField.CONFIGURATION: config.effective(),
        ScheduleField.JOBS: jobs,
        "python": str(python),
        "source_dependencies": list(SCRIPT_NAMES),
    }


def install(
    config: Config,
    source: Path,
    agents_directory: Path,
    runner: Runner,
    platform: str,
    activate: bool,
) -> Json:
    if sys.version_info[:2] not in SUPPORTED_PYTHON:
        raise ValueError(
            "Managed runtime requires a managed Python 3.13 or 3.14 interpreter"
        )
    plan = install_plan(
        config, source, Path(sys.executable).resolve(), agents_directory, platform
    )
    if plan[ScheduleField.STATUS] == "unsupported" or not activate:
        return plan
    installed_path = config.root / INSTALL_NAME
    prior = manifest(config.root)
    owned_paths = (
        {job["path"] for job in prior.get(ScheduleField.JOBS, [])}
        if isinstance(prior, dict)
        else set()
    )
    for job in plan[ScheduleField.JOBS]:
        path = Path(job["path"])
        if path.is_symlink() or (path.exists() and str(path) not in owned_paths):
            raise ValueError(
                f"Unowned launch agent exists: {path}; inspect it before installation"
            )
        if path.exists() and isinstance(prior, dict):
            old = next(
                item for item in prior[ScheduleField.JOBS] if item["path"] == str(path)
            )
            if path.read_bytes() != plistlib.dumps(old[ScheduleField.PLIST]):
                raise ValueError(
                    f"Managed launch agent changed externally: {path}; inspect it before replacement"
                )
    domain = f"gui/{os.getuid()}"
    assets = Path(plan[ScheduleField.ASSETS])
    assets.mkdir(parents=True, exist_ok=True)
    for name in SCRIPT_NAMES:
        destination = assets / name
        data = (source / name).read_bytes()
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError(
                f"Versioned asset changed externally: {destination}; inspect it before installation"
            )
        atomic_write(destination, data)
    json_write(config.root / CONFIG_NAME, config.effective())
    plan[ScheduleField.STATUS] = "installing"
    json_write(installed_path, plan)
    for job in plan[ScheduleField.JOBS]:
        path = Path(job["path"])
        atomic_write(path, plistlib.dumps(job[ScheduleField.PLIST]))
        if prior:
            result = runner.run(
                (LAUNCHCTL, LaunchctlOperation.PRINT, domain + "/" + job["label"])
            )
            if result.returncode == 0:
                checked(
                    runner,
                    (
                        LAUNCHCTL,
                        LaunchctlOperation.BOOTOUT,
                        domain + "/" + job["label"],
                    ),
                )
            elif not absent(result):
                raise RuntimeError(
                    f"Cannot establish managed job status: {result.stderr[:2000]}"
                )
        checked(runner, (LAUNCHCTL, LaunchctlOperation.BOOTSTRAP, domain, str(path)))
    plan[ScheduleField.STATUS] = "installed"
    plan["retention_gaps"] = retain_assets(config.root, assets)
    json_write(installed_path, plan)
    return plan


def retain_assets(root: Path, active: Path) -> list[str]:
    candidates: list[tuple[float, Path]] = []
    gaps: list[str] = []
    with os.scandir(root / "assets") as entries:
        for index, entry in enumerate(entries):
            if index >= 32:
                gaps.append(
                    "asset retention scan bound reached; additional entries remain uninspected"
                )
                break
            if (
                entry.is_symlink()
                or not entry.is_dir(follow_symlinks=False)
                or len(entry.name) != 64
                or any(c not in "0123456789abcdef" for c in entry.name)
            ):
                continue
            candidates.append(
                (entry.stat(follow_symlinks=False).st_mtime, Path(entry.path))
            )
    candidates.sort(reverse=True)
    keep = {active, *(path for _, path in candidates[:2])}
    for _, path in candidates:
        if path in keep:
            continue
        try:
            names: set[str] = set()
            with os.scandir(path) as children:
                for entry in children:
                    names.add(entry.name)
                    if len(names) > len(SCRIPT_NAMES):
                        break
            if names != set(SCRIPT_NAMES) or any(
                (path / name).is_symlink()
                or (path / name).stat().st_size > 2 * 1024 * 1024
                for name in SCRIPT_NAMES
            ):
                gaps.append(f"asset retention preserved unrecognized contents: {path}")
                continue
            payload = b"".join(
                name.encode() + (path / name).read_bytes() for name in SCRIPT_NAMES
            )
            if hashlib.sha256(payload).hexdigest() != path.name:
                gaps.append(f"asset retention preserved changed version: {path}")
                continue
            for name in SCRIPT_NAMES:
                (path / name).unlink()
            path.rmdir()
        except OSError as error:
            gaps.append(f"asset retention failed: {path}: {error}")
    return gaps


def jobs(root: Path, operation: str, runner: Runner, platform: str) -> Json:
    if platform != "darwin":
        return {
            ScheduleField.STATUS: JobStatus.UNSUPPORTED,
            "platform": platform,
            "operation": operation,
        }
    installation = root / INSTALL_NAME
    if not installation.exists():
        return {
            ScheduleField.STATUS: JobStatus.NOT_INSTALLED,
            "operation": operation,
            "root": str(root),
        }
    value = manifest(root)
    if value is None:
        return {ScheduleField.STATUS: JobStatus.NOT_INSTALLED, "operation": operation}
    domain = f"gui/{os.getuid()}"
    result: Json = {
        "operation": operation,
        "installation_status": value.get(ScheduleField.STATUS),
        ScheduleField.JOBS: [],
    }
    for job in value[ScheduleField.JOBS]:
        label, path = str(job["label"]), Path(job["path"])
        if label not in tuple(LABEL_PREFIX + "." + mode for mode in MODES):
            raise ValueError(
                f"Unrecognized managed label: {label}; inspect {installation}"
            )
        if path.name != label + ".plist" or path.is_symlink():
            raise ValueError(f"Invalid managed launch-agent path: {path}")
        handle = domain + "/" + label
        observed = runner.run((LAUNCHCTL, LaunchctlOperation.PRINT, handle))
        if observed.returncode and not absent(observed):
            result[ScheduleField.JOBS].append(
                {
                    "label": label,
                    ScheduleField.LOADED: None,
                    "returncode": observed.returncode,
                    "stdout": observed.stdout,
                    "stderr": observed.stderr,
                }
            )
            result[ScheduleField.STATUS] = JobStatus.FAILED
            continue
        if operation == JobOperation.STOP and observed.returncode == 0:
            observed = checked(runner, (LAUNCHCTL, LaunchctlOperation.BOOTOUT, handle))
        elif operation == JobOperation.RESTART:
            if not path.exists() or path.read_bytes() != plistlib.dumps(
                job[ScheduleField.PLIST]
            ):
                raise ValueError(
                    f"Managed launch agent unavailable or changed: {path}; reconcile installation first"
                )
            if observed.returncode == 0:
                checked(runner, (LAUNCHCTL, LaunchctlOperation.BOOTOUT, handle))
            checked(
                runner, (LAUNCHCTL, LaunchctlOperation.BOOTSTRAP, domain, str(path))
            )
            observed = runner.run((LAUNCHCTL, LaunchctlOperation.PRINT, handle))
        result[ScheduleField.JOBS].append(
            {
                "label": label,
                "returncode": observed.returncode,
                "stdout": observed.stdout,
                "stderr": observed.stderr,
                ScheduleField.LOADED: observed.returncode == 0
                if operation != JobOperation.STOP
                else False,
            }
        )
    if result.get(ScheduleField.STATUS) != JobStatus.FAILED:
        result[ScheduleField.STATUS] = (
            JobStatus.INSPECTED
            if operation == JobOperation.STATUS
            else JobStatus.COMPLETED
        )
    return result

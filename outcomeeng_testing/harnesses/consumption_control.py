"""Real local resources and controlled command-boundary evidence for usage control."""

from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.consumption_control import (
    spending_cases,
    invalid_amounts,
    growing_contexts,
    usage_snapshots,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
SCRIPTS = ROOT / "src/plugins/coding-agents/skills/control-token-spend/scripts"
FIXTURES = ROOT / "outcomeeng_testing/fixtures/consumption_control"
SEED = 2026100915
EXAMPLES = 80
REPLAY = "spx/43-coding-agents.enabler/18-consumption-control.enabler/tests/test_accounting.property.l1.py"


def modules() -> tuple[ModuleType, ModuleType, ModuleType, ModuleType]:
    result = []
    for name in (
        "usage_accounting",
        "usage_reports",
        "usage_schedule",
        "usage_control",
    ):
        location = SCRIPTS / (name + ".py")
        existing = sys.modules.get(name)
        if existing is not None:
            if Path(str(existing.__file__)).resolve() != location:
                raise RuntimeError(
                    f"Test module name already belongs to another source: {name}"
                )
            result.append(existing)
            continue
        spec = importlib.util.spec_from_file_location(name, location)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load shipped module: {location}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        result.append(module)
    return result[0], result[1], result[2], result[3]


def fixture() -> dict[str, Any]:
    return json.loads((FIXTURES / "assistant.json").read_text())


@dataclass(frozen=True)
class AccountingObservation:
    reconciled: tuple[int, ...]
    expected: tuple[int, ...]
    cost: Decimal
    oracle_cost: Decimal
    identity_stable: bool
    native_parent: str
    expected_parent: str
    child: bool


def accounting_observation(
    snapshots: tuple[tuple[int, ...], tuple[int, ...]],
) -> AccountingObservation:
    accounting, _, _, _ = modules()
    normalized = []
    source = (
        Path("/transcripts") / fixture()["sessionId"] / "subagents/agent-captured.jsonl"
    )
    for ordinal, tokens in enumerate(snapshots):
        row = fixture()
        row.pop("requestId", None) if not ordinal else None
        row["uuid"] += str(ordinal)
        usage = row["message"]["usage"]
        usage.update(zip(accounting.FIELDS, tokens, strict=True))
        usage["cache_creation"] = {
            "ephemeral_5m_input_tokens": 0,
            "ephemeral_1h_input_tokens": tokens[2],
        }
        value, _ = accounting.request(row, source)
        if value is None:
            raise RuntimeError("Generated positive usage was not normalized")
        normalized.append(value)
    result = accounting.reconcile(*normalized)
    components = accounting.cost(result)
    if components is None:
        raise RuntimeError("Captured standard model unexpectedly has no pricing")
    expected = tuple(max(a, b) for a, b in zip(*snapshots, strict=True))
    external = json.loads((FIXTURES / "pricing.json").read_text())["per_million"]
    rates = tuple(
        Decimal(external[key])
        for key in (
            "input_tokens",
            "cache_read_input_tokens",
            "ephemeral_1h_input_tokens",
            "output_tokens",
        )
    )
    oracle = sum(
        (Decimal(value) * rate for value, rate in zip(expected, rates, strict=True)),
        Decimal(),
    ) / Decimal(1_000_000)
    return AccountingObservation(
        tuple(result["tokens"]),
        expected,
        sum(components.values(), Decimal()),
        oracle,
        normalized[0]["identity"] == normalized[1]["identity"],
        result["parent"],
        fixture()["sessionId"],
        result["child"],
    )


def accounting_property(check: Callable[[AccountingObservation], None]) -> None:
    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(usage_snapshots())
    def run(snapshots: tuple[tuple[int, ...], tuple[int, ...]]) -> None:
        check(accounting_observation(snapshots))

    run_replayable_property(run, seed_value=SEED, replay_path=REPLAY)


@dataclass(frozen=True)
class SignalObservation:
    actual_kinds: set[str]
    expected_kinds: set[str]
    identities: tuple[str, ...]
    repeated_identities: tuple[str, ...]
    configured_alert: Decimal
    actual_alert: Decimal
    expected_pace: Decimal
    actual_pace: Decimal | None
    conversion: object


def signal_observation(case: tuple[int, int, int]) -> SignalObservation:
    accounting, _, _, _ = modules()
    amount, budget, elapsed = case
    reset = accounting.timestamp(fixture()["timestamp"])
    end = reset + dt.timedelta(seconds=elapsed)
    config = accounting.Config(
        Path("/state"), Path("/transcripts"), reset, weekly_budget=Decimal(budget)
    )
    current = {
        "start_utc": accounting.iso(end - accounting.QUARTER),
        "end_exclusive_utc": accounting.iso(end),
        "api_equivalent_usd": amount,
        "gaps": [],
    }
    weekly = dict(current, start_utc=accounting.iso(reset))
    found = accounting.signals(config, current, weekly, end)
    repeated = accounting.signals(config, current, weekly, end)
    expected = set()
    if Decimal(amount) >= config.alert:
        expected.add(accounting.SignalKind.ROLLING_THRESHOLD)
    if Decimal(amount) >= Decimal(budget):
        expected.add(accounting.SignalKind.WEEKLY_BUDGET)
    pace = (
        Decimal(budget)
        * Decimal(elapsed)
        / Decimal(str(accounting.WEEK.total_seconds()))
    )
    if Decimal(amount) >= pace:
        expected.add(accounting.SignalKind.WEEKLY_PACE)
    observed_pace = next(
        (
            Decimal(value["ceiling_usd"])
            for value in found
            if value["kind"] == accounting.SignalKind.WEEKLY_PACE
        ),
        None,
    )
    return SignalObservation(
        {value["kind"] for value in found},
        expected,
        tuple(value["identity"] for value in found),
        tuple(value["identity"] for value in repeated),
        config.alert,
        Decimal(config.effective()[accounting.ALERT_ENV]),
        pace,
        observed_pace,
        next((value["subscription_usage_conversion"] for value in found), None),
    )


def signal_property(check: Callable[[SignalObservation], None]) -> None:
    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(spending_cases())
    def run(case: tuple[int, int, int]) -> None:
        check(signal_observation(case))

    run_replayable_property(
        run, seed_value=SEED, replay_path=REPLAY.replace("accounting", "signals")
    )


def configuration_property(check: Callable[[list[tuple[str, str]]], None]) -> None:
    accounting, _, _, _ = modules()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(invalid_amounts())
    def run(amount: str) -> None:
        diagnostics = []
        for field in (accounting.ALERT_ENV, accounting.BUDGET_ENV):
            environment = {accounting.RESET_ENV: fixture()["timestamp"], field: amount}
            try:
                accounting.Config.from_environment(
                    environment, Path("/state"), Path("/transcripts")
                )
                diagnostics.append((field, ""))
            except ValueError as error:
                diagnostics.append((field, str(error)))
        check(diagnostics)

    run_replayable_property(
        run, seed_value=SEED, replay_path=REPLAY.replace("accounting", "configuration")
    )


@dataclass
class Workspace:
    root: Path
    projects: Path
    config: Any
    start: dt.datetime
    end: dt.datetime
    source: Path
    payload: bytes


@contextmanager
def workspace() -> Iterator[Workspace]:
    accounting, _, _, _ = modules()
    with TemporaryDirectory(prefix="consumption-evidence-") as temporary:
        root = Path(temporary)
        projects = root / "transcripts"
        projects.mkdir()
        row = fixture()
        start = accounting.timestamp(row["timestamp"]) - accounting.HOUR
        end = accounting.timestamp(row["timestamp"]) + accounting.HOUR
        config = accounting.Config(root / "state", projects, start)
        source = projects / (row["sessionId"] + ".jsonl")
        payload = (json.dumps(row) + "\n").encode()
        source.write_bytes(payload)
        yield Workspace(root, projects, config, start, end, source, payload)


@dataclass(frozen=True)
class CollectionObservation:
    before: str
    after: str
    first_requests: int
    after_requests: int
    expected_requests: int
    resumed_usage: tuple[int, ...]
    expected_usage: tuple[int, ...]
    partial_gaps: list[str]
    start_boundary_requests: int
    excluded_boundary_requests: int
    expected_excluded: int
    child_requests: int
    expected_children: int
    byte_bound: int
    bytes_read: int


def collection_observation(work: Workspace) -> CollectionObservation:
    accounting, _, _, _ = modules()
    cut = len(work.payload) // 2
    work.source.write_bytes(work.payload[:cut])
    before = hashlib.sha256(work.source.read_bytes()).hexdigest()
    with accounting.Evidence(work.config) as evidence:
        first = evidence.collect(work.end)
        partial = evidence.measure(work.start, work.end)
    after = hashlib.sha256(work.source.read_bytes()).hexdigest()
    with work.source.open("ab") as stream:
        stream.write(work.payload[cut:])
        stream.write(work.payload)
    child = work.projects / fixture()["sessionId"] / "subagents/agent-captured.jsonl"
    child.parent.mkdir(parents=True)
    child.write_bytes(work.payload)
    with accounting.Evidence(work.config) as evidence:
        for _ in range(4):
            collected = evidence.collect(work.end)
        measured = evidence.measure(work.start, work.end)
        stamp = accounting.timestamp(fixture()["timestamp"])
        included = evidence.measure(stamp, work.end)
        excluded = evidence.measure(work.start, stamp)
    expected = tuple(
        fixture()["message"]["usage"][key] * 2 for key in accounting.FIELDS
    )
    return CollectionObservation(
        before,
        after,
        partial["requests"],
        measured["requests"],
        2,
        tuple(measured[key] for key in accounting.TOKEN_KEYS),
        expected,
        first["gaps"],
        included["requests"],
        excluded["requests"],
        0,
        measured["child_requests"],
        1,
        accounting.MAX_BYTES,
        collected["bytes_read"],
    )


@dataclass(frozen=True)
class ReportObservation:
    json_usage: tuple[int, ...]
    measured_usage: tuple[int, ...]
    csv_usage: tuple[int, ...]
    links: tuple[str, ...]
    document: str
    retained_excerpt_size: int
    excerpt_bound: int
    unknown_conversion: object
    temporary_files: tuple[Path, ...]


def report_observation(work: Workspace) -> ReportObservation:
    import csv

    accounting, reports, _, _ = modules()
    captured = json.loads((FIXTURES / "behavior.json").read_text())
    with work.source.open("ab") as stream:
        for row in captured["records"]:
            stream.write((json.dumps(row) + "\n").encode())
    with accounting.Evidence(work.config) as evidence:
        evidence.collect(work.end)
        measured = evidence.measure(work.start, work.end)
        screened = reports.behavior(evidence, measured)
        path = reports.write_report(work.config.root, measured, screened)
    actual = json.loads((path.parent / reports.MEASUREMENT_NAME).read_text())[
        "measurement"
    ]
    with (path.parent / reports.CSV_NAME).open() as stream:
        rows = list(csv.DictReader(stream))
    return ReportObservation(
        tuple(actual[key] for key in accounting.TOKEN_KEYS),
        tuple(measured[key] for key in accounting.TOKEN_KEYS),
        tuple(sum(int(row[key]) for row in rows) for key in accounting.TOKEN_KEYS),
        tuple("evidence.html#" + key for key in screened["references"]),
        path.read_text(),
        max(
            (len(value["excerpt"]) for value in screened["references"].values()),
            default=0,
        ),
        accounting.EXCERPT_CHARS,
        actual["subscription_usage_conversion"],
        tuple(path.parent.glob(".usage-*")),
    )


class RecordingRunner:
    """Stage 5 interaction-protocol and failure-simulation collaborator; no shared jobs."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, ...]] = []
        self.loaded: set[str] = set()

    def run(self, argv: tuple[str, ...], timeout: float = 30) -> Any:
        _, _, schedule, _ = modules()
        self.calls.append(argv)
        if self.fail:
            return schedule.CommandResult(argv, 77, "", "permission denied")
        if argv[1] == "bootstrap":
            self.loaded.add(Path(argv[-1]).stem)
        elif argv[1] == "bootout":
            self.loaded.discard(argv[-1].rsplit("/", 1)[-1])
        elif argv[1] == "print" and argv[-1].rsplit("/", 1)[-1] not in self.loaded:
            return schedule.CommandResult(argv, 113, "", "Could not find service")
        return schedule.CommandResult(argv, 0, "state = waiting", "")


@dataclass(frozen=True)
class InstallationObservation:
    owned_assets: set[str]
    expected_assets: set[str]
    stable_arguments: list[list[str]]
    stable_root: str
    source_root: str
    stopped_loaded: list[bool]
    restarted_loaded: list[bool]
    failed_status: str
    expected_failed_status: str
    unknown_loaded: list[object]
    calls: tuple[tuple[str, ...], ...]


def installation_observation(work: Workspace) -> InstallationObservation:
    _, _, schedule, _ = modules()
    runner = RecordingRunner()
    agents = work.root / "launch-agents"
    plan = schedule.install(work.config, SCRIPTS, agents, runner, "darwin", True)
    stopped = schedule.jobs(work.config.root, "stop", runner, "darwin")
    restarted = schedule.jobs(work.config.root, "restart", runner, "darwin")
    failed = schedule.jobs(
        work.config.root, "status", RecordingRunner(fail=True), "darwin"
    )
    return InstallationObservation(
        {path.name for path in Path(plan["assets"]).iterdir()},
        set(schedule.SCRIPT_NAMES),
        [job["plist"]["ProgramArguments"] for job in plan["jobs"]],
        str(work.config.root),
        str(SCRIPTS),
        [job["loaded"] for job in stopped["jobs"]],
        [job["loaded"] for job in restarted["jobs"]],
        failed["status"],
        schedule.JobStatus.FAILED,
        [job["loaded"] for job in failed["jobs"]],
        tuple(runner.calls),
    )


@dataclass(frozen=True)
class NativeInstallationObservation:
    status: str
    expected_status: str
    installed_loaded: tuple[object, ...]
    stopped_loaded: tuple[object, ...]
    restarted_loaded: tuple[object, ...]
    cleanup_loaded: tuple[object, ...]


def native_installation_observation(work: Workspace) -> NativeInstallationObservation:
    _, _, schedule, _ = modules()
    runner = schedule.SubprocessRunner()
    if sys.platform != "darwin":
        status = schedule.jobs(work.config.root, "status", runner, sys.platform)
        return NativeInstallationObservation(
            status["status"], schedule.JobStatus.UNSUPPORTED, (), (), (), ()
        )
    domain = f"gui/{os.getuid()}"
    for mode in schedule.MODES:
        handle = domain + "/" + schedule.LABEL_PREFIX + "." + mode
        observed = runner.run(("/bin/launchctl", "print", handle))
        if not schedule.absent(observed):
            raise RuntimeError(
                f"Native installation verification requires an absent job: {handle}; "
                f"existing service or indeterminate state is preserved: {observed.stderr}"
            )
    stopped: dict[str, Any] = {}
    restarted: dict[str, Any] = {}
    installed: dict[str, Any] = {}
    cleanup: dict[str, Any] = {}
    try:
        schedule.install(
            work.config,
            SCRIPTS,
            work.root / "native-launch-agents",
            runner,
            sys.platform,
            True,
        )
        installed = schedule.jobs(work.config.root, "status", runner, sys.platform)
        stopped = schedule.jobs(work.config.root, "stop", runner, sys.platform)
        restarted = schedule.jobs(work.config.root, "restart", runner, sys.platform)
    finally:
        cleanup = schedule.jobs(work.config.root, "stop", runner, sys.platform)
        if cleanup["status"] != schedule.JobStatus.COMPLETED:
            raise RuntimeError(f"Native installation cleanup failed: {cleanup}")
    return NativeInstallationObservation(
        installed["status"],
        schedule.JobStatus.COMPLETED,
        tuple(job["loaded"] for job in installed["jobs"]),
        tuple(job["loaded"] for job in stopped["jobs"]),
        tuple(job["loaded"] for job in restarted["jobs"]),
        tuple(job["loaded"] for job in cleanup["jobs"]),
    )


@dataclass(frozen=True)
class StandaloneObservation:
    exitcode: int
    expected_exitcode: int
    model_invocations: int
    artifact: Path
    source_before: str
    source_after: str
    optional_status: str
    expected_optional_status: str
    request_count: int
    expected_requests: int


def standalone_observation(work: Workspace) -> StandaloneObservation:
    accounting, _, schedule, _ = modules()
    assets = work.root / "copied-assets"
    assets.mkdir()
    for name in schedule.SCRIPT_NAMES:
        shutil.copyfile(SCRIPTS / name, assets / name)
    before = hashlib.sha256(work.source.read_bytes()).hexdigest()
    empty_path = work.root / "empty-path"
    empty_path.mkdir()
    result = subprocess.run(
        (
            sys.executable,
            "-S",
            "-B",
            str(assets / "usage_control.py"),
            "report",
            "--root",
            str(work.config.root),
            "--projects",
            str(work.projects),
            "--start",
            accounting.iso(work.start),
            "--end",
            accounting.iso(work.end),
            "--aise",
            str(empty_path / "absent-aise"),
            "--aise-database",
            str(empty_path / "absent-database"),
        ),
        env={"PATH": str(empty_path), accounting.RESET_ENV: accounting.iso(work.start)},
        cwd=work.root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if not result.stdout:
        raise RuntimeError(f"Standalone worker emitted no result: {result.stderr}")
    response = json.loads(result.stdout)
    artifact = Path(response["artifact"])
    envelope = json.loads((artifact.parent / "measurements.json").read_text())
    return StandaloneObservation(
        result.returncode,
        0,
        response["model_invocations"],
        artifact,
        before,
        hashlib.sha256(work.source.read_bytes()).hexdigest(),
        envelope["measurement"]["investigation"]["status"],
        schedule.InvestigationStatus.UNAVAILABLE,
        response["requests"],
        1,
    )


@dataclass(frozen=True)
class LockObservation:
    status: str
    expected_status: str
    exitcode: int
    expected_exitcode: int
    state_exists: bool


def lock_observation(work: Workspace) -> LockObservation:
    accounting, _, _, control = modules()
    work.config.root.mkdir()
    with (work.config.root / accounting.LOCK_NAME).open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        environment = {
            "PATH": os.defpath,
            accounting.RESET_ENV: accounting.iso(work.start),
        }
        result = subprocess.run(
            (
                sys.executable,
                "-B",
                str(SCRIPTS / "usage_control.py"),
                "collect",
                "--root",
                str(work.config.root),
                "--projects",
                str(work.projects),
                "--end",
                accounting.iso(work.end),
            ),
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    response = json.loads(result.stdout)
    return LockObservation(
        response["status"],
        control.OVERLAP_STATUS,
        result.returncode,
        control.SUCCESS_EXIT,
        (work.config.root / accounting.STATE_NAME).exists(),
    )


@dataclass(frozen=True)
class ContextObservation:
    requests: int
    expected_requests: int
    early_context: float
    late_context: float
    early_cost: float
    late_cost: float
    growth: float
    cost_growth: float


def context_property(check: Callable[[ContextObservation], None]) -> None:
    accounting, _, _, _ = modules()
    with workspace() as work, accounting.Evidence(work.config) as evidence:

        @seed(SEED)
        @settings(max_examples=EXAMPLES, deadline=None)
        @given(growing_contexts())
        def run(factors: list[int]) -> None:
            with evidence.db:
                evidence.db.execute("DELETE FROM requests")
                for ordinal, factor in enumerate(factors):
                    row = fixture()
                    row["message"]["id"] += str(ordinal)
                    row["timestamp"] = accounting.iso(
                        accounting.timestamp(row["timestamp"])
                        + dt.timedelta(seconds=ordinal)
                    )
                    usage = row["message"]["usage"]
                    for field in accounting.FIELDS:
                        usage[field] *= factor
                    for field in usage["cache_creation"]:
                        usage["cache_creation"][field] *= factor
                    evidence.ingest(row, work.source, work.start, work.end)
            value = evidence.measure(work.start, work.end)["sessions"][
                fixture()["sessionId"]
            ]
            check(
                ContextObservation(
                    value["requests"],
                    len(factors),
                    value["early_context_mean"],
                    value["late_context_mean"],
                    value["early_cost_mean"],
                    value["late_cost_mean"],
                    value["context_growth_ratio"],
                    value["cost_growth_ratio"],
                )
            )

        run_replayable_property(
            run,
            seed_value=SEED,
            replay_path=REPLAY.replace("accounting.property.l1", "context.property.l2"),
        )


@dataclass(frozen=True)
class DetectorObservation:
    first_count: int
    second_count: int
    durable_count: int
    first_identities: tuple[str, ...]
    second_identities: tuple[str, ...]
    existing_statuses: tuple[str, ...]
    expected_existing_status: str
    source_before: str
    source_after: str


def detector_observation(work: Workspace) -> DetectorObservation:
    accounting, _, _, control = modules()
    row = fixture()
    native, _ = accounting.request(row, work.source)
    components = accounting.cost(native)
    amount = sum(components.values(), Decimal())
    factor = int(work.config.alert / amount) + 1
    usage = row["message"]["usage"]
    for field in accounting.FIELDS:
        usage[field] *= factor
    for field in usage["cache_creation"]:
        usage["cache_creation"][field] *= factor
    work.source.write_bytes((json.dumps(row) + "\n").encode())
    end = accounting.timestamp(row["timestamp"]) + dt.timedelta(seconds=1)
    before = hashlib.sha256(work.source.read_bytes()).hexdigest()
    args = control.parser().parse_args([control.OPERATIONS[2]])
    first = control.worker(args, work.config, end, RecordingRunner())
    second = control.worker(args, work.config, end, RecordingRunner())
    return DetectorObservation(
        len(first["signals"]),
        len(second["signals"]),
        len(tuple((work.config.root / "alerts").glob("*.json"))),
        tuple(value["identity"] for value in first["signals"]),
        tuple(value["identity"] for value in second["signals"]),
        tuple(value["status"] for value in second["signals"]),
        control.ALREADY_RECORDED_STATUS,
        before,
        hashlib.sha256(work.source.read_bytes()).hexdigest(),
    )


@dataclass(frozen=True)
class RetentionObservation:
    remaining: int
    ceiling: int
    preserved_foreign: bool
    report_gaps: list[str]
    alerts_before: int
    alerts_after: int
    expected_after: int


def retention_observation(work: Workspace) -> RetentionObservation:
    accounting, reports, _, _ = modules()
    with accounting.Evidence(work.config) as evidence:
        evidence.collect(work.end)
        measured = evidence.measure(work.start, work.end)
        screened = reports.behavior(evidence, measured)
    directory = work.config.root / "reports"
    foreign = directory / hashlib.sha256(b"operator-owned-directory").hexdigest()
    foreign.mkdir(parents=True)
    (foreign / "operator-owned.txt").write_text("Preserve this operator-owned content.")
    os.utime(foreign, (0, 0))
    for ordinal in range(reports.MAX_REPORTS + 2):
        measured["retention_sequence"] = ordinal
        reports.write_report(work.config.root, measured, screened)
    gaps = json.loads((work.config.root / "retention-status.json").read_text())[
        "report_gaps"
    ]
    detector = detector_observation(work)
    alerts_before = detector.durable_count
    reports.retain_alerts(
        work.config.root,
        accounting.iso(work.end + dt.timedelta(days=accounting.RETENTION_DAYS)),
    )
    return RetentionObservation(
        len(tuple(directory.iterdir())),
        reports.MAX_REPORTS + 1,
        (foreign / "operator-owned.txt").is_file(),
        gaps,
        alerts_before,
        len(tuple((work.config.root / "alerts").glob("*.json"))),
        0,
    )

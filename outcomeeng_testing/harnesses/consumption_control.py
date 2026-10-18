"""Real local resources and controlled command-boundary evidence for usage control."""

from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
from html.parser import HTMLParser
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import astuple, dataclass, replace
from enum import StrEnum
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any
from uuid import uuid4

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng.distribution.shipped_scripts import load_shipped_module
from outcomeeng_testing.generators.consumption_control import (
    spending_cases,
    invalid_amounts,
    invalid_rates,
    override_rates,
    growing_contexts,
    usage_snapshots,
    unsupported_models,
    duration_snapshots,
    alert_reads,
    distinct_namespace_pairs,
    invalid_namespaces,
    non_list_retained_values,
    non_mapping_retained_entries,
    nonconforming_plist_paths,
    valid_namespaces,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
SCRIPTS = ROOT / "dist/claude/coding-agents/skills/control-token-spend/scripts"
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
        result.append(load_shipped_module(name, location))
    return result[0], result[1], result[2], result[3]


AccountingField = modules()[0].AccountingField
ControlField = modules()[3].ControlField
ReportField = modules()[1].ReportField
ScheduleField = modules()[2].ScheduleField


def fixture() -> dict[str, Any]:
    value = json.loads((FIXTURES / "assistant.json").read_text())
    if not isinstance(value, dict):
        raise TypeError("Transcript fixture must be a JSON object")
    return value


def published_number(value: int | float | Decimal | None, style: str) -> str:
    """Independent standard-library formatting oracle over the public policy."""
    reports = modules()[1]
    if value is None:
        return str(reports.UNKNOWN_NUMBER)
    return (
        str(reports.NUMBER_PREFIXES.get(style, ""))
        + format(value, style)
        + str(reports.NUMBER_SUFFIXES.get(style, ""))
    )


@dataclass(frozen=True)
class AccountingObservation:
    normalized: tuple[dict[str, Any] | None, ...]
    reconciled: dict[str, Any] | None
    components: dict[str, Decimal] | None
    snapshots: tuple[tuple[int, ...], tuple[int, ...]]
    rates: tuple[Decimal, ...]
    fields: Any
    expected_parent: str


def accounting_observation(
    snapshots: tuple[tuple[int, ...], tuple[int, ...]],
) -> AccountingObservation:
    accounting, _, _, _ = modules()
    normalized = []
    source = (
        Path("/transcripts")
        / fixture()[AccountingField.SESSIONID]
        / accounting.SUBAGENT_DIRECTORY
        / "agent-captured.jsonl"
    )
    for ordinal, counters in enumerate(snapshots):
        row = fixture()
        row[AccountingField.UUID] += str(ordinal)
        usage = row[AccountingField.MESSAGE][AccountingField.USAGE]
        tokens = (counters[0], counters[1], counters[2] + counters[3], counters[4])
        usage.update(zip(accounting.FIELDS, tokens, strict=True))
        usage[AccountingField.CACHE_CREATION] = {
            AccountingField.EPHEMERAL_5M_INPUT_TOKENS: counters[2],
            AccountingField.EPHEMERAL_1H_INPUT_TOKENS: counters[3],
        }
        value, _ = accounting.request(row, source, accounting.bundled_prices())
        normalized.append(value)
    result = (
        accounting.reconcile(*normalized)
        if all(value is not None for value in normalized)
        else None
    )
    components = (
        accounting.cost(result, accounting.bundled_prices())
        if result is not None
        else None
    )
    external = json.loads((FIXTURES / "pricing.json").read_text())["per_million"]
    rates = tuple(
        Decimal(external[key])
        for key in (
            "input_tokens",
            "cache_read_input_tokens",
            "ephemeral_5m_input_tokens",
            "ephemeral_1h_input_tokens",
            "output_tokens",
        )
    )
    return AccountingObservation(
        tuple(normalized),
        result,
        components,
        snapshots,
        rates,
        AccountingField,
        fixture()[AccountingField.SESSIONID],
    )


def accounting_property(check: Callable[[AccountingObservation], None]) -> None:
    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(duration_snapshots())
    def run(snapshots: tuple[tuple[int, ...], tuple[int, ...]]) -> None:
        check(accounting_observation(snapshots))

    run_replayable_property(run, seed_value=SEED, replay_path=REPLAY)


@dataclass(frozen=True)
class SignalObservation:
    actual_kinds: set[str]
    amount: Decimal
    budget: Decimal
    kinds: Any
    records: tuple[dict[str, Any], ...]
    current_window: tuple[str, str]
    weekly_window: tuple[str, str]
    configuration: dict[str, Any]
    fields: Any
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
    reset = accounting.timestamp(fixture()[AccountingField.TIMESTAMP])
    end = reset + dt.timedelta(seconds=elapsed)
    config = accounting.Config(
        Path("/state"), Path("/transcripts"), reset, weekly_budget=Decimal(budget)
    )
    current = {
        AccountingField.START_UTC: accounting.iso(end - accounting.QUARTER),
        AccountingField.END_EXCLUSIVE_UTC: accounting.iso(end),
        AccountingField.API_EQUIVALENT_USD: amount,
        AccountingField.GAPS: [],
    }
    weekly = current | {AccountingField.START_UTC: accounting.iso(reset)}
    found = accounting.signals(config, current, weekly, end)
    repeated = accounting.signals(config, current, weekly, end)
    pace = (
        Decimal(budget)
        * Decimal(elapsed)
        / Decimal(str(accounting.WEEK.total_seconds()))
    )
    observed_pace = next(
        (
            Decimal(value[AccountingField.CEILING_USD])
            for value in found
            if value[AccountingField.KIND] == accounting.SignalKind.WEEKLY_PACE
        ),
        None,
    )
    return SignalObservation(
        {value[AccountingField.KIND] for value in found},
        Decimal(amount),
        Decimal(budget),
        accounting.SignalKind,
        tuple(found),
        (
            current[AccountingField.START_UTC],
            current[AccountingField.END_EXCLUSIVE_UTC],
        ),
        (weekly[AccountingField.START_UTC], weekly[AccountingField.END_EXCLUSIVE_UTC]),
        config.effective(),
        AccountingField,
        tuple(value[AccountingField.IDENTITY] for value in found),
        tuple(value[AccountingField.IDENTITY] for value in repeated),
        config.alert,
        Decimal(config.effective()[accounting.ALERT_ENV]),
        pace,
        observed_pace,
        next(
            (value[AccountingField.SUBSCRIPTION_USAGE_CONVERSION] for value in found),
            None,
        ),
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
            environment = {
                accounting.RESET_ENV: fixture()[AccountingField.TIMESTAMP],
                field: amount,
            }
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


def valid_namespace_property(check: Callable[[str, str, str], None]) -> None:
    """Resolve each valid namespace through the environment and the saved effective configuration."""
    accounting, _, _, _ = modules()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(valid_namespaces())
    def run(namespace: str) -> None:
        environment = {
            accounting.RESET_ENV: fixture()[AccountingField.TIMESTAMP],
            accounting.NAMESPACE_ENV: namespace,
        }
        config = accounting.Config.from_environment(
            environment, Path("/state"), Path("/transcripts")
        )
        check(
            namespace,
            config.namespace,
            config.effective()[accounting.NAMESPACE_ENV],
        )

    run_replayable_property(
        run, seed_value=SEED, replay_path=REPLAY.replace("accounting", "configuration")
    )


def invalid_namespace_property(check: Callable[[tuple[str, str]], None]) -> None:
    accounting, _, _, _ = modules()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(invalid_namespaces(accounting.NAMESPACE_MAX_CHARS))
    def run(namespace: str) -> None:
        environment = {
            accounting.RESET_ENV: fixture()[AccountingField.TIMESTAMP],
            accounting.NAMESPACE_ENV: namespace,
        }
        try:
            accounting.Config.from_environment(
                environment, Path("/state"), Path("/transcripts")
            )
            check((accounting.NAMESPACE_ENV, ""))
        except ValueError as error:
            check((accounting.NAMESPACE_ENV, str(error)))

    run_replayable_property(
        run, seed_value=SEED, replay_path=REPLAY.replace("accounting", "configuration")
    )


class NamespaceRoute(StrEnum):
    """The two operator-facing routes by which a namespace reaches the merged configuration."""

    SAVED = "saved installation configuration"
    OPTION = "--launchd-namespace"


@contextmanager
def _without_usage_environment() -> Iterator[None]:
    held = {
        key: os.environ.pop(key)
        for key in list(os.environ)
        if key.startswith("SPX_USAGE_")
    }
    try:
        yield
    finally:
        os.environ.update(held)


def _routed_configuration(route: NamespaceRoute, namespace: str) -> Any:
    """Merge one namespace through usage_control.configuration() by the given route."""
    accounting, _, _, control = modules()
    reset = fixture()[AccountingField.TIMESTAMP]
    with (
        TemporaryDirectory(prefix="namespace-route-") as temporary,
        _without_usage_environment(),
    ):
        root = Path(temporary)
        arguments = [control.Option.ROOT, str(root), control.Option.END, reset]
        if route is NamespaceRoute.SAVED:
            (root / control.CONFIG_NAME).write_text(
                json.dumps(
                    {accounting.RESET_ENV: reset, accounting.NAMESPACE_ENV: namespace}
                ),
                encoding="utf-8",
            )
        else:
            arguments += [control.Option.RESET_AT, reset]
            arguments.append(f"{control.Option.LAUNCHD_NAMESPACE}={namespace}")
        args = control.parser().parse_args(arguments)
        return control.configuration(args, accounting.timestamp(reset))


def valid_routed_namespace_property(
    check: Callable[[NamespaceRoute, str, str], None],
) -> None:
    """Drive each valid namespace through usage_control.configuration() by each route."""
    accounting, _, _, _ = modules()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(valid_namespaces())
    def run(namespace: str) -> None:
        for route in NamespaceRoute:
            config = _routed_configuration(route, namespace)
            check(route, namespace, config.effective()[accounting.NAMESPACE_ENV])

    run_replayable_property(
        run, seed_value=SEED, replay_path=REPLAY.replace("accounting", "configuration")
    )


def invalid_routed_namespace_property(
    check: Callable[[NamespaceRoute, str, tuple[str, str]], None],
) -> None:
    """Drive each invalid namespace through usage_control.configuration() by each route;
    the observation is the rejection message, empty when the namespace was accepted."""
    accounting, _, _, _ = modules()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(invalid_namespaces(accounting.NAMESPACE_MAX_CHARS))
    def run(namespace: str) -> None:
        for route in NamespaceRoute:
            try:
                _routed_configuration(route, namespace)
                check(route, namespace, (accounting.NAMESPACE_ENV, ""))
            except ValueError as error:
                check(route, namespace, (accounting.NAMESPACE_ENV, str(error)))

    run_replayable_property(
        run, seed_value=SEED, replay_path=REPLAY.replace("accounting", "configuration")
    )


@dataclass(frozen=True)
class PriceOverrideObservation:
    written: tuple[str, ...]
    resolved: tuple[Decimal, ...]
    bundled_others: dict[str, Any]
    resolved_others: dict[str, Any]
    written_file: str
    effective_file: object


def _write_override(directory: Path, model: str, rates: dict[str, object]) -> Path:
    accounting, _, _, _ = modules()
    path = directory / "price-override.json"
    path.write_text(
        json.dumps({accounting.PRICE_DOCUMENT_KEY: {model: rates}}), encoding="utf-8"
    )
    return path


def _override_config(path: Path) -> Any:
    accounting, _, _, _ = modules()
    environment = {
        accounting.RESET_ENV: fixture()[AccountingField.TIMESTAMP],
        accounting.PRICE_OVERRIDE_ENV: str(path),
    }
    return accounting.Config.from_environment(
        environment, Path("/state"), Path("/transcripts")
    )


def price_override_property(check: Callable[[PriceOverrideObservation], None]) -> None:
    accounting, _, _, _ = modules()
    bundled = accounting.bundled_prices()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(st.sampled_from(sorted(bundled)), override_rates())
    def run(model: str, rates: tuple[str, ...]) -> None:
        with TemporaryDirectory(prefix="price-override-") as temporary:
            path = _write_override(
                Path(temporary),
                model,
                dict(zip(accounting.PRICE_CLASSES, rates, strict=True)),
            )
            config = _override_config(path)
            check(
                PriceOverrideObservation(
                    rates,
                    astuple(config.prices[model]),
                    {name: price for name, price in bundled.items() if name != model},
                    {
                        name: price
                        for name, price in config.prices.items()
                        if name != model
                    },
                    str(path.resolve()),
                    config.effective()[accounting.PRICE_OVERRIDE_ENV],
                )
            )

    run_replayable_property(
        run, seed_value=SEED, replay_path=REPLAY.replace("accounting", "configuration")
    )


def invalid_price_override_property(
    check: Callable[[tuple[str, str]], None],
) -> None:
    accounting, _, _, _ = modules()
    bundled = accounting.bundled_prices()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(
        st.sampled_from(sorted(bundled)),
        override_rates(),
        st.sampled_from(accounting.PRICE_CLASSES),
        invalid_rates(),
    )
    def run(model: str, rates: tuple[str, ...], rejected: str, value: object) -> None:
        entry: dict[str, object] = dict(
            zip(accounting.PRICE_CLASSES, rates, strict=True)
        )
        entry[rejected] = value
        location = (
            f"{accounting.PRICE_OVERRIDE_ENV}: "
            f"{accounting.PRICE_DOCUMENT_KEY}.{model}.{rejected}"
        )
        with TemporaryDirectory(prefix="price-override-") as temporary:
            path = _write_override(Path(temporary), model, entry)
            try:
                _override_config(path)
                check((location, ""))
            except ValueError as error:
                check((location, str(error)))

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
        start = accounting.timestamp(row[AccountingField.TIMESTAMP]) - accounting.HOUR
        end = accounting.timestamp(row[AccountingField.TIMESTAMP]) + accounting.HOUR
        config = accounting.Config(root / "state", projects, start)
        source = projects / (row[AccountingField.SESSIONID] + ".jsonl")
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
    child = (
        work.projects
        / fixture()[AccountingField.SESSIONID]
        / accounting.SUBAGENT_DIRECTORY
        / "agent-captured.jsonl"
    )
    child.parent.mkdir(parents=True)
    child.write_bytes(work.payload)
    with accounting.Evidence(work.config) as evidence:
        collected = evidence.collect(work.end)
        for _ in range(1, 4):
            collected = evidence.collect(work.end)
        measured = evidence.measure(work.start, work.end)
        stamp = accounting.timestamp(fixture()[AccountingField.TIMESTAMP])
        included = evidence.measure(stamp, work.end)
        excluded = evidence.measure(work.start, stamp)
    expected = tuple(
        fixture()[AccountingField.MESSAGE][AccountingField.USAGE][key] * 2
        for key in accounting.FIELDS
    )
    return CollectionObservation(
        before,
        after,
        partial[AccountingField.REQUESTS],
        measured[AccountingField.REQUESTS],
        2,
        tuple(measured[key] for key in accounting.TOKEN_KEYS),
        expected,
        first[AccountingField.GAPS],
        included[AccountingField.REQUESTS],
        excluded[AccountingField.REQUESTS],
        0,
        measured[AccountingField.CHILD_REQUESTS],
        1,
        accounting.MAX_BYTES,
        collected[AccountingField.BYTES_READ],
    )


class ReportReader(HTMLParser):
    """Read the actual HTML element text independently of the renderer."""

    def __init__(self) -> None:
        super().__init__()
        self.section = ""
        self.capture = ""
        self.text = ""
        self.row: list[str] = []
        self.rows: dict[str, list[tuple[str, ...]]] = {}
        self.headlines: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("summary", "td", "strong"):
            self.capture, self.text = tag, ""
        if tag == "tr":
            self.row = []

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == self.capture:
            if tag == "summary":
                self.section = self.text
            elif tag == "td":
                self.row.append(self.text)
            elif tag == "strong":
                self.headlines.append(self.text)
            self.capture = ""
        if tag == "tr" and self.row:
            self.rows.setdefault(self.section, []).append(tuple(self.row))
        if tag == "details":
            self.section = ""


@dataclass(frozen=True)
class ReportObservation:
    html_rows: dict[str, list[tuple[str, ...]]]
    measurement: dict[str, Any]
    fields: Any
    sections: Any
    formats: Any
    display: Callable[..., str]
    token_keys: tuple[str, ...]
    headline_values: tuple[str, ...]
    verified_outputs: object
    unknown_output_text: str
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
        ReportField.MEASUREMENT
    ]
    with (path.parent / reports.CSV_NAME).open() as stream:
        rows = list(csv.DictReader(stream))
    reader = ReportReader()
    reader.feed(path.read_text())
    sections = reports.ReportSection
    return ReportObservation(
        reader.rows,
        measured,
        AccountingField,
        sections,
        reports.NumberFormat,
        published_number,
        accounting.TOKEN_KEYS,
        tuple(reader.headlines),
        actual[AccountingField.VERIFIED_OUTPUTS],
        reports.UNKNOWN_OUTPUT,
        tuple(actual[key] for key in accounting.TOKEN_KEYS),
        tuple(measured[key] for key in accounting.TOKEN_KEYS),
        tuple(sum(int(row[key]) for row in rows) for key in accounting.TOKEN_KEYS),
        tuple(
            reports.EVIDENCE_NAME + "#" + key
            for key in screened[ReportField.REFERENCES]
        ),
        path.read_text(),
        max(
            (
                len(value[AccountingField.EXCERPT])
                for value in screened[ReportField.REFERENCES].values()
            ),
            default=0,
        ),
        accounting.EXCERPT_CHARS,
        actual[AccountingField.SUBSCRIPTION_USAGE_CONVERSION],
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
        if argv[1] == schedule.LaunchctlOperation.BOOTSTRAP:
            self.loaded.add(Path(argv[-1]).stem)
        elif argv[1] == schedule.LaunchctlOperation.BOOTOUT:
            self.loaded.discard(argv[-1].rsplit("/", 1)[-1])
        elif (
            argv[1] == schedule.LaunchctlOperation.PRINT
            and argv[-1].rsplit("/", 1)[-1] not in self.loaded
        ):
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
    inactive_assets_exist: bool
    inactive_calls: tuple[tuple[str, ...], ...]


def installation_observation(work: Workspace) -> InstallationObservation:
    _, _, schedule, _ = modules()
    runner = RecordingRunner()
    agents = work.root / "launch-agents"
    inactive = schedule.install(work.config, SCRIPTS, agents, runner, "darwin", False)
    inactive_assets_exist = Path(inactive[ScheduleField.ASSETS]).exists()
    inactive_calls = tuple(runner.calls)
    plan = schedule.install(work.config, SCRIPTS, agents, runner, "darwin", True)
    stopped = schedule.jobs(
        work.config.root, schedule.JobOperation.STOP, runner, "darwin"
    )
    restarted = schedule.jobs(
        work.config.root, schedule.JobOperation.RESTART, runner, "darwin"
    )
    failed = schedule.jobs(
        work.config.root,
        schedule.JobOperation.STATUS,
        RecordingRunner(fail=True),
        "darwin",
    )
    return InstallationObservation(
        {path.name for path in Path(plan[ScheduleField.ASSETS]).iterdir()},
        set(schedule.ASSET_NAMES),
        [
            job[ScheduleField.PLIST][ScheduleField.PROGRAMARGUMENTS]
            for job in plan[ScheduleField.JOBS]
        ],
        str(work.config.root),
        str(SCRIPTS),
        [job[ScheduleField.LOADED] for job in stopped[ScheduleField.JOBS]],
        [job[ScheduleField.LOADED] for job in restarted[ScheduleField.JOBS]],
        failed[ScheduleField.STATUS],
        schedule.JobStatus.FAILED,
        [job[ScheduleField.LOADED] for job in failed[ScheduleField.JOBS]],
        tuple(runner.calls),
        inactive_assets_exist,
        inactive_calls,
    )


@dataclass(frozen=True)
class NativeInstallationObservation:
    status: str
    expected_status: str
    expected_job_count: int
    installed_loaded: tuple[object, ...]
    stopped_loaded: tuple[object, ...]
    restarted_loaded: tuple[object, ...]
    cleanup_loaded: tuple[object, ...]


def native_installation_observation(work: Workspace) -> NativeInstallationObservation:
    _, _, schedule, _ = modules()
    runner = schedule.SubprocessRunner()
    if sys.platform != "darwin":
        status = schedule.jobs(
            work.config.root, schedule.JobOperation.STATUS, runner, sys.platform
        )
        return NativeInstallationObservation(
            status[ScheduleField.STATUS],
            schedule.JobStatus.UNSUPPORTED,
            0,
            (),
            (),
            (),
            (),
        )
    domain = f"gui/{os.getuid()}"
    config = replace(work.config, namespace=f"{work.config.namespace}-{uuid4().hex}")
    for mode in schedule.MODES:
        handle = domain + "/" + schedule.job_label(config.namespace, mode)
        observed = runner.run(
            (schedule.LAUNCHCTL, schedule.LaunchctlOperation.PRINT, handle)
        )
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
            config,
            SCRIPTS,
            work.root / "native-launch-agents",
            runner,
            sys.platform,
            True,
        )
        installed = schedule.jobs(
            work.config.root, schedule.JobOperation.STATUS, runner, sys.platform
        )
        schedule.jobs(
            work.config.root, schedule.JobOperation.STOP, runner, sys.platform
        )
        stopped = schedule.jobs(
            work.config.root, schedule.JobOperation.STATUS, runner, sys.platform
        )
        restarted = schedule.jobs(
            work.config.root, schedule.JobOperation.RESTART, runner, sys.platform
        )
    finally:
        cleanup = schedule.jobs(
            work.config.root, schedule.JobOperation.STOP, runner, sys.platform
        )
        if cleanup[ScheduleField.STATUS] != schedule.JobStatus.COMPLETED:
            raise RuntimeError(f"Native installation cleanup failed: {cleanup}")
        cleanup = schedule.jobs(
            work.config.root, schedule.JobOperation.STATUS, runner, sys.platform
        )
    return NativeInstallationObservation(
        installed[ScheduleField.STATUS],
        schedule.JobStatus.INSPECTED,
        len(schedule.MODES),
        tuple(job[ScheduleField.LOADED] for job in installed[ScheduleField.JOBS]),
        tuple(job[ScheduleField.LOADED] for job in stopped[ScheduleField.JOBS]),
        tuple(job[ScheduleField.LOADED] for job in restarted[ScheduleField.JOBS]),
        tuple(job[ScheduleField.LOADED] for job in cleanup[ScheduleField.JOBS]),
    )


class InvestigationRunner:
    """Stage 5 version-mismatch and existing-index interaction boundary."""

    def __init__(self, version: str) -> None:
        self.version = version
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: tuple[str, ...], timeout: int = 30) -> Any:
        _, _, schedule, _ = modules()
        self.calls.append(argv)
        output = (
            self.version if argv[-1] == schedule.AISE_VERSION_OPTION else json.dumps([])
        )
        return schedule.CommandResult(argv, 0, output, "")


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
    incompatible_status: str
    expected_incompatible_status: str
    incompatible_calls: tuple[tuple[str, ...], ...]
    expected_version_calls: tuple[tuple[str, ...], ...]
    queried_status: str
    expected_queried_status: str
    query_calls: tuple[tuple[str, ...], ...]
    expected_query_calls: tuple[tuple[str, ...], ...]


def standalone_observation(work: Workspace) -> StandaloneObservation:
    accounting, _, schedule, _ = modules()
    assets = work.root / "copied-assets"
    assets.mkdir()
    for name in schedule.ASSET_NAMES:
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
            modules()[3].OPERATIONS[1],
            modules()[3].Option.ROOT,
            str(work.config.root),
            modules()[3].Option.PROJECTS,
            str(work.projects),
            modules()[3].Option.START,
            accounting.iso(work.start),
            modules()[3].Option.END,
            accounting.iso(work.end),
            modules()[3].Option.AISE,
            str(empty_path / "absent-aise"),
            modules()[3].Option.AISE_DATABASE,
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
    artifact = Path(response[ControlField.ARTIFACT])
    envelope = json.loads((artifact.parent / modules()[1].MEASUREMENT_NAME).read_text())
    executable = work.root / "selected-investigator"
    database = work.root / "selected-index"
    executable.write_text("Protocol collaborator; never executed.")
    database.write_text("Existing index; never refreshed.")
    measured = envelope[ReportField.MEASUREMENT]
    incompatible_runner = InvestigationRunner(schedule.AISE_VERSION + "-incompatible")
    incompatible = schedule.investigate(
        incompatible_runner, executable, database, measured
    )
    query_runner = InvestigationRunner(schedule.AISE_VERSION)
    queried = schedule.investigate(query_runner, executable, database, measured)
    version_calls = ((str(executable.resolve()), schedule.AISE_VERSION_OPTION),)
    query_call = (
        str(executable.resolve()),
        schedule.AISE_DATABASE_OPTION,
        str(database.resolve()),
        *schedule.AISE_QUERY_PREFIX,
        schedule.AISE_START_OPTION,
        measured[AccountingField.START_UTC],
        schedule.AISE_END_OPTION,
        measured[AccountingField.END_EXCLUSIVE_UTC],
        *schedule.AISE_QUERY_SUFFIX,
    )
    return StandaloneObservation(
        result.returncode,
        0,
        response[ReportField.MODEL_INVOCATIONS],
        artifact,
        before,
        hashlib.sha256(work.source.read_bytes()).hexdigest(),
        envelope[ReportField.MEASUREMENT][ControlField.INVESTIGATION][
            ScheduleField.STATUS
        ],
        schedule.InvestigationStatus.UNAVAILABLE,
        response[AccountingField.REQUESTS],
        1,
        incompatible[ScheduleField.STATUS],
        schedule.InvestigationStatus.INCOMPATIBLE,
        tuple(incompatible_runner.calls),
        version_calls,
        queried[ScheduleField.STATUS],
        schedule.InvestigationStatus.QUERIED,
        tuple(query_runner.calls),
        (*version_calls, query_call),
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
                control.OPERATIONS[0],
                modules()[3].Option.ROOT,
                str(work.config.root),
                modules()[3].Option.PROJECTS,
                str(work.projects),
                modules()[3].Option.END,
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
        response[ScheduleField.STATUS],
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
    factors: tuple[int, ...]
    sample_limit: int
    sample_divisor: int
    unit_context: int
    unit_cost: float
    measurement: dict[str, Any]
    fields: Any
    unit_components: dict[str, float]
    token_keys: tuple[str, ...]


def context_property(check: Callable[[ContextObservation], None]) -> None:
    accounting, _, _, _ = modules()
    captured = fixture()[AccountingField.MESSAGE][AccountingField.USAGE]
    prices = json.loads((FIXTURES / "pricing.json").read_text())["per_million"]
    input_tokens, cache_read_tokens, _, output_tokens = accounting.FIELDS
    independent_components = (
        Decimal(captured[input_tokens]) * Decimal(prices[input_tokens]),
        Decimal(captured[cache_read_tokens]) * Decimal(prices[cache_read_tokens]),
        sum(
            (
                Decimal(captured[AccountingField.CACHE_CREATION][key])
                * Decimal(prices[key])
                for key in (
                    AccountingField.EPHEMERAL_5M_INPUT_TOKENS,
                    AccountingField.EPHEMERAL_1H_INPUT_TOKENS,
                )
            ),
            Decimal(),
        ),
        Decimal(captured[output_tokens]) * Decimal(prices[output_tokens]),
    )
    oracle_components = dict(
        zip(
            accounting.TOKEN_KEYS,
            (float(value / Decimal(1_000_000)) for value in independent_components),
            strict=True,
        )
    )
    with workspace() as work, accounting.Evidence(work.config) as evidence:

        @seed(SEED)
        @settings(max_examples=EXAMPLES, deadline=None)
        @given(growing_contexts())
        def run(factors: list[int]) -> None:
            with evidence.db:
                evidence.db.execute("DELETE FROM requests")
                for ordinal, factor in enumerate(factors):
                    row = fixture()
                    row[AccountingField.MESSAGE][AccountingField.ID] += str(ordinal)
                    row[AccountingField.TIMESTAMP] = accounting.iso(
                        accounting.timestamp(row[AccountingField.TIMESTAMP])
                        + dt.timedelta(seconds=ordinal)
                    )
                    usage = row[AccountingField.MESSAGE][AccountingField.USAGE]
                    for field in accounting.FIELDS:
                        usage[field] *= factor
                    for field in usage[AccountingField.CACHE_CREATION]:
                        usage[AccountingField.CACHE_CREATION][field] *= factor
                    evidence.ingest(row, work.source, work.start, work.end)
            measurement = evidence.measure(work.start, work.end)
            value = measurement[AccountingField.SESSIONS][
                fixture()[AccountingField.SESSIONID]
            ]
            check(
                ContextObservation(
                    value[AccountingField.REQUESTS],
                    len(factors),
                    value[AccountingField.EARLY_CONTEXT_MEAN],
                    value[AccountingField.LATE_CONTEXT_MEAN],
                    value[AccountingField.EARLY_COST_MEAN],
                    value[AccountingField.LATE_COST_MEAN],
                    value[AccountingField.CONTEXT_GROWTH_RATIO],
                    value[AccountingField.COST_GROWTH_RATIO],
                    tuple(factors),
                    accounting.CONTEXT_SAMPLE_LIMIT,
                    accounting.CONTEXT_SAMPLE_DIVISOR,
                    sum(captured[key] for key in accounting.FIELDS[:3]),
                    float(sum(independent_components, Decimal()) / Decimal(1_000_000)),
                    measurement,
                    AccountingField,
                    oracle_components,
                    accounting.TOKEN_KEYS,
                )
            )

        run_replayable_property(
            run,
            seed_value=SEED,
            replay_path=REPLAY.replace("accounting.property.l1", "context.property.l2"),
        )


@dataclass(frozen=True)
class DetectorObservation:
    durable_records: tuple[dict[str, Any], ...]
    emitted_configuration: dict[str, Any]
    emitted_window: tuple[str, str]
    configuration: dict[str, Any]
    expected_window: tuple[str, str]
    fields: Any
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
    native, _ = accounting.request(row, work.source, work.config.prices)
    components = accounting.cost(native, work.config.prices)
    amount = sum(components.values(), Decimal())
    factor = int(work.config.alert / amount) + 1
    usage = row[AccountingField.MESSAGE][AccountingField.USAGE]
    for field in accounting.FIELDS:
        usage[field] *= factor
    for field in usage[AccountingField.CACHE_CREATION]:
        usage[AccountingField.CACHE_CREATION][field] *= factor
    work.source.write_bytes((json.dumps(row) + "\n").encode())
    end = accounting.timestamp(row[AccountingField.TIMESTAMP]) + dt.timedelta(seconds=1)
    before = hashlib.sha256(work.source.read_bytes()).hexdigest()
    args = control.parser().parse_args([control.OPERATIONS[2]])
    first = control.worker(args, work.config, end, RecordingRunner())
    second = control.worker(args, work.config, end, RecordingRunner())
    return DetectorObservation(
        tuple(
            json.loads(path.read_text())[ControlField.SIGNAL]
            for path in (work.config.root / modules()[1].ALERT_DIRECTORY).glob("*.json")
        ),
        first[AccountingField.CONFIGURATION],
        (first[AccountingField.START_UTC], first[AccountingField.END_EXCLUSIVE_UTC]),
        work.config.effective(),
        (accounting.iso(end - accounting.QUARTER), accounting.iso(end)),
        AccountingField,
        len(first[ControlField.SIGNALS]),
        len(second[ControlField.SIGNALS]),
        len(tuple((work.config.root / modules()[1].ALERT_DIRECTORY).glob("*.json"))),
        tuple(value[AccountingField.IDENTITY] for value in first[ControlField.SIGNALS]),
        tuple(
            value[AccountingField.IDENTITY] for value in second[ControlField.SIGNALS]
        ),
        tuple(value[ScheduleField.STATUS] for value in second[ControlField.SIGNALS]),
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
    directory = work.config.root / reports.REPORT_DIRECTORY
    foreign = directory / hashlib.sha256(b"operator-owned-directory").hexdigest()
    foreign.mkdir(parents=True)
    (foreign / "operator-owned.txt").write_text("Preserve this operator-owned content.")
    os.utime(foreign, (0, 0))
    for ordinal in range(reports.MAX_REPORTS + 2):
        measured["retention_sequence"] = ordinal
        reports.write_report(work.config.root, measured, screened)
    gaps = json.loads((work.config.root / reports.RETENTION_NAME).read_text())[
        ReportField.REPORT_GAPS
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
        len(tuple((work.config.root / modules()[1].ALERT_DIRECTORY).glob("*.json"))),
        0,
    )


@dataclass(frozen=True)
class UnknownPricingObservation:
    model: str
    normalization_gaps: list[str]
    components: object
    measured_gaps: list[str]
    unpriced_requests: int
    expected_requests: int
    measured_usage: tuple[int, ...]
    generated_usage: tuple[int, ...]


def unknown_pricing_property(
    check: Callable[[UnknownPricingObservation], None],
) -> None:
    accounting, _, _, _ = modules()
    with workspace() as work, accounting.Evidence(work.config) as evidence:
        ordinal = 0

        @seed(SEED)
        @settings(max_examples=EXAMPLES, deadline=None)
        @given(unsupported_models(), usage_snapshots())
        def run(model: str, snapshots: tuple[tuple[int, ...], tuple[int, ...]]) -> None:
            nonlocal ordinal
            row = fixture()
            stamp = work.start + dt.timedelta(seconds=ordinal + 1)
            ordinal += 1
            row[AccountingField.TIMESTAMP] = accounting.iso(stamp)
            row[AccountingField.MESSAGE][AccountingField.ID] += str(ordinal)
            row[AccountingField.MESSAGE][AccountingField.MODEL] = model
            usage = row[AccountingField.MESSAGE][AccountingField.USAGE]
            usage.update(zip(accounting.FIELDS, snapshots[0], strict=True))
            usage[AccountingField.CACHE_CREATION] = {
                AccountingField.EPHEMERAL_5M_INPUT_TOKENS: 0,
                AccountingField.EPHEMERAL_1H_INPUT_TOKENS: snapshots[0][2],
            }
            value, gaps = accounting.request(row, work.source, work.config.prices)
            with evidence.db:
                evidence.ingest(row, work.source, work.start, work.end)
            measured = evidence.measure(stamp, stamp + dt.timedelta(seconds=1))
            check(
                UnknownPricingObservation(
                    model,
                    gaps,
                    accounting.cost(value, work.config.prices),
                    measured[AccountingField.GAPS],
                    measured[AccountingField.UNPRICED_REQUESTS],
                    1,
                    tuple(measured[key] for key in accounting.TOKEN_KEYS),
                    snapshots[0],
                )
            )

        run_replayable_property(run, seed_value=SEED, replay_path=REPLAY)


@dataclass(frozen=True)
class BoundObservation:
    prefixes: Any
    complete: tuple[bool, ...]
    bytes_read: int
    byte_limit: int
    gaps: list[str]
    first_offset_total: int
    persisted_offset_total: int
    resumed_offset_total: int
    clock_gaps: list[str]
    clock_bytes: int
    resumed_clock_requests: int
    expected_clock_requests: int
    discovery_cursor: int
    discovery_gaps: list[str]
    capacity_gaps: list[str]


def collection_bounds_observation() -> BoundObservation:
    accounting, _, _, _ = modules()
    with workspace() as work:
        # Actual production byte ceiling, with one more file than the byte page holds.
        for index in range(accounting.MAX_BYTES // accounting.MAX_CHUNK + 1):
            target = work.projects / (str(index) + ".jsonl")
            target.write_bytes(
                work.payload + b" " * (accounting.MAX_CHUNK - len(work.payload) + 1)
            )
        with accounting.Evidence(work.config) as evidence:
            first = evidence.collect(work.end)
            first_offsets = int(
                evidence.db.execute("SELECT SUM(offset) FROM files").fetchone()[0]
            )
        with accounting.Evidence(work.config) as evidence:
            persisted = int(
                evidence.db.execute("SELECT SUM(offset) FROM files").fetchone()[0]
            )
            evidence.collect(work.end)
            resumed = int(
                evidence.db.execute("SELECT SUM(offset) FROM files").fetchone()[0]
            )
    with workspace() as work:
        ticks = iter((0.0, float(accounting.MAX_SECONDS + 1)))

        def clock() -> float:
            return next(ticks, float(accounting.MAX_SECONDS + 1))

        with accounting.Evidence(work.config, clock=clock) as evidence:
            timed = evidence.collect(work.end)
        with accounting.Evidence(work.config) as evidence:
            evidence.collect(work.end)
            resumed_requests = evidence.measure(work.start, work.end)[
                AccountingField.REQUESTS
            ]
    with workspace() as work:
        # Directory-entry ceiling applies to all entries, including non-transcripts.
        for index in range(accounting.MAX_ENTRIES + 1):
            (work.projects / (str(index) + ".inert")).touch()
        with accounting.Evidence(work.config) as evidence:
            discovery = evidence.collect(work.end)
            cursor = int(
                evidence.db.execute(
                    "SELECT cursor FROM directories WHERE path=?",
                    (str(work.config.projects),),
                ).fetchone()[0]
            )
        with accounting.Evidence(work.config) as evidence:
            capacity = evidence.collect(work.end)
    return BoundObservation(
        accounting.CollectionGap,
        tuple(
            value[AccountingField.HISTORY_COMPLETE]
            for value in (first, timed, discovery, capacity)
        ),
        first[AccountingField.BYTES_READ],
        accounting.MAX_BYTES,
        first[AccountingField.GAPS],
        first_offsets,
        persisted,
        resumed,
        timed[AccountingField.GAPS],
        timed[AccountingField.BYTES_READ],
        resumed_requests,
        1,
        cursor,
        discovery[AccountingField.GAPS],
        capacity[AccountingField.GAPS],
    )


@dataclass(frozen=True)
class AlertReadObservation:
    fields: Any
    statuses: Any
    stored: tuple[tuple[str, dt.datetime, str, dict[str, Any]], ...]
    cutoff: dt.datetime
    result: dict[str, Any]
    root: Path
    state_before: dict[str, bytes]
    state_after: dict[str, bytes]
    journal_after: bytes


def _state_files(root: Path) -> dict[str, bytes]:
    """Snapshot durable state; SQLite reader sidecars hold no state and are excluded."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.name.endswith(("-shm", "-wal"))
    }


def _journal(root: Path) -> bytes:
    journal = root / (modules()[0].STATE_NAME + "-wal")
    return journal.read_bytes() if journal.exists() else b""


def alert_read_observation(
    case: tuple[list[tuple[str, int, int]], int],
) -> AlertReadObservation:
    accounting, _, _, _ = modules()
    records, cutoff_offset = case
    base = accounting.timestamp(fixture()[AccountingField.TIMESTAMP])
    with TemporaryDirectory(prefix="alert-read-") as temporary:
        root = Path(temporary) / "state"
        config = accounting.Config(root, Path(temporary) / "transcripts", base)
        stored = tuple(
            (
                identity,
                base + dt.timedelta(seconds=offset),
                accounting.iso(base + dt.timedelta(seconds=offset)),
                {
                    AccountingField.KIND: accounting.SignalKind.ROLLING_THRESHOLD.value,
                    AccountingField.API_EQUIVALENT_USD: str(amount),
                },
            )
            for identity, offset, amount in records
        )
        with accounting.Evidence(config) as evidence, evidence.db:
            for identity, _, stamp, signal in stored:
                evidence.db.execute(
                    "INSERT INTO signals VALUES(?,?,?)",
                    (identity, accounting.encoded(signal), stamp),
                )
        before = _state_files(root)
        cutoff = base + dt.timedelta(seconds=cutoff_offset)
        result = accounting.recorded_alerts(root, cutoff)
        return AlertReadObservation(
            AccountingField,
            accounting.AlertReadStatus,
            stored,
            cutoff,
            result,
            root,
            before,
            _state_files(root),
            _journal(root),
        )


def alert_read_property(check: Callable[[AlertReadObservation], None]) -> None:
    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(alert_reads())
    def run(case: tuple[list[tuple[str, int, int]], int]) -> None:
        check(alert_read_observation(case))

    run_replayable_property(
        run,
        seed_value=SEED,
        replay_path=REPLAY.replace("accounting.property.l1", "alerts.mapping.l1"),
    )


@dataclass(frozen=True)
class UnreadableAlertObservation:
    fields: Any
    statuses: Any
    root: Path
    result: dict[str, Any]
    state_before: dict[str, bytes]
    state_after: dict[str, bytes]


def unreadable_alert_observations() -> Iterator[UnreadableAlertObservation]:
    """Yield a read of an absent detector state and of a state that is no database."""
    accounting, _, _, _ = modules()
    base = accounting.timestamp(fixture()[AccountingField.TIMESTAMP])
    for corrupt in (False, True):
        with TemporaryDirectory(prefix="alert-unreadable-") as temporary:
            root = Path(temporary) / "state"
            root.mkdir()
            if corrupt:
                (root / accounting.STATE_NAME).write_bytes(b"not a database" * 64)
            before = _state_files(root)
            result = accounting.recorded_alerts(root, base)
            yield UnreadableAlertObservation(
                AccountingField,
                accounting.AlertReadStatus,
                root,
                result,
                before,
                _state_files(root),
            )


@dataclass(frozen=True)
class NamespaceScopeObservation:
    namespace: str
    foreign_labels: frozenset[str]
    installed_labels: tuple[str, ...]
    touched_labels: tuple[str, ...]
    loaded_after: frozenset[str]


def namespace_scope_property(
    check: Callable[[NamespaceScopeObservation], None],
) -> None:
    """Install, inspect, stop, and restart under one namespace beside another's jobs."""
    _, _, schedule, _ = modules()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(distinct_namespace_pairs())
    def run(namespaces: tuple[str, str]) -> None:
        namespace, foreign = namespaces
        with workspace() as work:
            config = replace(work.config, namespace=namespace)
            runner = RecordingRunner()
            foreign_labels = frozenset(
                schedule.job_label(foreign, mode) for mode in schedule.MODES
            )
            runner.loaded.update(foreign_labels)
            plan = schedule.install(
                config, SCRIPTS, work.root / "launch-agents", runner, "darwin", True
            )
            for operation in (
                schedule.JobOperation.STATUS,
                schedule.JobOperation.STOP,
                schedule.JobOperation.RESTART,
            ):
                schedule.jobs(config.root, operation, runner, "darwin")
            check(
                NamespaceScopeObservation(
                    namespace,
                    foreign_labels,
                    tuple(str(job["label"]) for job in plan[ScheduleField.JOBS]),
                    tuple(
                        Path(call[-1]).stem
                        if call[1] == schedule.LaunchctlOperation.BOOTSTRAP
                        else call[-1].rsplit("/", 1)[-1]
                        for call in runner.calls
                    ),
                    frozenset(runner.loaded),
                )
            )

    run_replayable_property(
        run,
        seed_value=SEED,
        replay_path=REPLAY.replace(
            "accounting.property.l1", "installation.compliance.l1"
        ),
    )


@dataclass(frozen=True)
class NamespaceReturnObservation:
    first: str
    second: str
    namespace_key: str
    record_after: dict[str, Any]
    first_labels: frozenset[str]
    second_labels: frozenset[str]
    second_files_before: dict[str, bytes]
    second_files_after: dict[str, bytes]
    return_labels: frozenset[str]
    loaded_after_return: frozenset[str]


def namespace_return_property(
    check: Callable[[NamespaceReturnObservation], None],
) -> None:
    """Install under one namespace, then another, then the first again against the same
    root. An install that raises propagates to the linked test."""
    accounting, _, schedule, _ = modules()

    def addressed(calls: Iterable[tuple[str, ...]]) -> frozenset[str]:
        return frozenset(
            Path(call[-1]).stem
            if call[1] == schedule.LaunchctlOperation.BOOTSTRAP
            else call[-1].rsplit("/", 1)[-1]
            for call in calls
        )

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(distinct_namespace_pairs())
    def run(namespaces: tuple[str, str]) -> None:
        first, second = namespaces
        with workspace() as work:
            runner = RecordingRunner()
            agents = work.root / "launch-agents"
            schedule.install(
                replace(work.config, namespace=first),
                SCRIPTS,
                agents,
                runner,
                "darwin",
                True,
            )
            second_plan = schedule.install(
                replace(work.config, namespace=second),
                SCRIPTS,
                agents,
                runner,
                "darwin",
                True,
            )
            second_paths = tuple(
                Path(job["path"]) for job in second_plan[ScheduleField.JOBS]
            )
            second_files_before = {
                str(path): path.read_bytes() for path in second_paths
            }
            mark = len(runner.calls)
            schedule.install(
                replace(work.config, namespace=first),
                SCRIPTS,
                agents,
                runner,
                "darwin",
                True,
            )
            check(
                NamespaceReturnObservation(
                    first,
                    second,
                    accounting.NAMESPACE_ENV,
                    json.loads((work.config.root / schedule.INSTALL_NAME).read_text()),
                    frozenset(
                        schedule.job_label(first, mode) for mode in schedule.MODES
                    ),
                    frozenset(
                        schedule.job_label(second, mode) for mode in schedule.MODES
                    ),
                    second_files_before,
                    {str(path): path.read_bytes() for path in second_paths},
                    addressed(runner.calls[mark:]),
                    frozenset(runner.loaded),
                )
            )

    run_replayable_property(
        run,
        seed_value=SEED,
        replay_path=REPLAY.replace(
            "accounting.property.l1", "installation.compliance.l1"
        ),
    )


@dataclass(frozen=True)
class NamespaceReinstallObservation:
    first: str
    second: str
    namespace_key: str
    record_after: dict[str, Any]
    first_labels: frozenset[str]
    second_labels: frozenset[str]
    first_files_before: dict[str, bytes]
    first_files_after: dict[str, bytes]
    loaded_after_install: frozenset[str]
    loaded_after_stop: frozenset[str]
    loaded_after_restart: frozenset[str]
    reinstall_labels: frozenset[str]
    status_labels: frozenset[str]
    stop_labels: frozenset[str]
    restart_labels: frozenset[str]


def namespace_reinstall_property(
    check: Callable[[NamespaceReinstallObservation], None],
) -> None:
    """Install under one namespace, reinstall under another against the same root,
    then inspect, stop, and restart through the installation record."""
    accounting, _, schedule, _ = modules()

    def addressed(calls: Iterable[tuple[str, ...]]) -> frozenset[str]:
        return frozenset(
            Path(call[-1]).stem
            if call[1] == schedule.LaunchctlOperation.BOOTSTRAP
            else call[-1].rsplit("/", 1)[-1]
            for call in calls
        )

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(distinct_namespace_pairs())
    def run(namespaces: tuple[str, str]) -> None:
        first, second = namespaces
        with workspace() as work:
            runner = RecordingRunner()
            agents = work.root / "launch-agents"
            first_plan = schedule.install(
                replace(work.config, namespace=first),
                SCRIPTS,
                agents,
                runner,
                "darwin",
                True,
            )
            first_paths = tuple(
                Path(job["path"]) for job in first_plan[ScheduleField.JOBS]
            )
            first_files_before = {str(path): path.read_bytes() for path in first_paths}
            mark = len(runner.calls)
            schedule.install(
                replace(work.config, namespace=second),
                SCRIPTS,
                agents,
                runner,
                "darwin",
                True,
            )
            reinstall_labels = addressed(runner.calls[mark:])
            loaded_after_install = frozenset(runner.loaded)
            labels: dict[str, frozenset[str]] = {}
            loaded: dict[str, frozenset[str]] = {}
            for operation in (
                schedule.JobOperation.STATUS,
                schedule.JobOperation.STOP,
                schedule.JobOperation.RESTART,
            ):
                mark = len(runner.calls)
                schedule.jobs(work.config.root, operation, runner, "darwin")
                labels[operation] = addressed(runner.calls[mark:])
                loaded[operation] = frozenset(runner.loaded)
            check(
                NamespaceReinstallObservation(
                    first,
                    second,
                    accounting.NAMESPACE_ENV,
                    json.loads((work.config.root / schedule.INSTALL_NAME).read_text()),
                    frozenset(
                        schedule.job_label(first, mode) for mode in schedule.MODES
                    ),
                    frozenset(
                        schedule.job_label(second, mode) for mode in schedule.MODES
                    ),
                    first_files_before,
                    {str(path): path.read_bytes() for path in first_paths},
                    loaded_after_install,
                    loaded[schedule.JobOperation.STOP],
                    loaded[schedule.JobOperation.RESTART],
                    reinstall_labels,
                    labels[schedule.JobOperation.STATUS],
                    labels[schedule.JobOperation.STOP],
                    labels[schedule.JobOperation.RESTART],
                )
            )

    run_replayable_property(
        run,
        seed_value=SEED,
        replay_path=REPLAY.replace(
            "accounting.property.l1", "installation.compliance.l1"
        ),
    )


@dataclass(frozen=True)
class MalformedRetainedRecordObservation:
    record_path: str
    field: str
    rejected_path: str
    message: str


def malformed_retained_record_property(
    check: Callable[[MalformedRetainedRecordObservation], None],
) -> None:
    """Install under one namespace, then another, so the installation record carries the
    first namespace's jobs as retained jobs; give one retained entry a non-conforming
    path and read the record. The observation is the rejection message, empty when the
    record was accepted. Any exception other than ValueError propagates to the linked test."""
    _, _, schedule, _ = modules()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(distinct_namespace_pairs(), st.data())
    def run(namespaces: tuple[str, str], data: st.DataObject) -> None:
        first, second = namespaces
        with workspace() as work:
            runner = RecordingRunner()
            agents = work.root / "launch-agents"
            for namespace in (first, second):
                schedule.install(
                    replace(work.config, namespace=namespace),
                    SCRIPTS,
                    agents,
                    runner,
                    "darwin",
                    True,
                )
            record_path = work.config.root / schedule.INSTALL_NAME
            record = json.loads(record_path.read_text())
            index = data.draw(st.integers(0, len(record[schedule.RETAINED_JOBS]) - 1))
            entry = record[schedule.RETAINED_JOBS][index]
            rejected = data.draw(
                nonconforming_plist_paths(str(agents), str(entry["label"]))
            )
            entry["path"] = rejected
            record_path.write_text(json.dumps(record), encoding="utf-8")
            try:
                schedule.manifest(work.config.root)
                message = ""
            except ValueError as error:
                message = str(error)
            check(
                MalformedRetainedRecordObservation(
                    str(record_path), schedule.RETAINED_JOBS, rejected, message
                )
            )

    run_replayable_property(
        run,
        seed_value=SEED,
        replay_path=REPLAY.replace(
            "accounting.property.l1", "installation.compliance.l1"
        ),
    )


class RetainedRecordMalformation(StrEnum):
    MISSING_PATH = "missing_path"
    NON_LIST_VALUE = "non_list_value"
    NON_MAPPING_ENTRY = "non_mapping_entry"


@dataclass(frozen=True)
class MalformedRetainedFieldObservation:
    record_path: str
    field: str
    message: str


def malformed_retained_field_property(
    malformation: RetainedRecordMalformation,
    check: Callable[[MalformedRetainedFieldObservation], None],
) -> None:
    """Install under one namespace, then another, so the installation record carries
    retained jobs; apply ``malformation`` to the retained jobs field and read the
    record. The observation is the rejection message, empty when the record was
    accepted. Any exception other than ValueError propagates to the linked test."""
    _, _, schedule, _ = modules()

    @seed(SEED)
    @settings(max_examples=EXAMPLES, deadline=None)
    @given(distinct_namespace_pairs(), st.data())
    def run(namespaces: tuple[str, str], data: st.DataObject) -> None:
        first, second = namespaces
        with workspace() as work:
            runner = RecordingRunner()
            agents = work.root / "launch-agents"
            for namespace in (first, second):
                schedule.install(
                    replace(work.config, namespace=namespace),
                    SCRIPTS,
                    agents,
                    runner,
                    "darwin",
                    True,
                )
            record_path = work.config.root / schedule.INSTALL_NAME
            record = json.loads(record_path.read_text())
            retained = record[schedule.RETAINED_JOBS]
            index = data.draw(st.integers(0, len(retained) - 1))
            if malformation is RetainedRecordMalformation.MISSING_PATH:
                del retained[index]["path"]
            elif malformation is RetainedRecordMalformation.NON_LIST_VALUE:
                record[schedule.RETAINED_JOBS] = data.draw(non_list_retained_values())
            else:
                retained[index] = data.draw(non_mapping_retained_entries())
            record_path.write_text(json.dumps(record), encoding="utf-8")
            try:
                schedule.manifest(work.config.root)
                message = ""
            except ValueError as error:
                message = str(error)
            check(
                MalformedRetainedFieldObservation(
                    str(record_path), schedule.RETAINED_JOBS, message
                )
            )

    run_replayable_property(
        run,
        seed_value=SEED,
        replay_path=REPLAY.replace(
            "accounting.property.l1", "installation.compliance.l1"
        ),
    )

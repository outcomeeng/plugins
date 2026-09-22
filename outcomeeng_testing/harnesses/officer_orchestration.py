"""Test infrastructure for the officer-ledger derivation entry point."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TextIO, cast

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng_testing.generators.officer_orchestration import (
    change_identifiers,
    duration_series,
    foreign_argument_vectors,
    foreign_read_causes,
    journal_carriers,
    leading_record_counts,
    mail_carriers,
    non_ledger_bodies,
    pass_labels,
    read_details,
    repeated_run_series,
    spend_series,
    store_message_ids,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPOSITORY_ROOT = Path(__file__).parents[2]
LEDGER_SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "src/plugins/coding-agents/skills/orchestrate-officers/scripts/derive_ledger.py"
)
LEDGER_MODULE_NAME = "coding_agents_officer_ledger"
PROPERTY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/32-officer-orchestration.enabler/tests/"
    "test_ledger_derivation.property.l1.py"
)
MAPPING_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/32-officer-orchestration.enabler/tests/"
    "test_ledger_derivation.mapping.l1.py"
)
SPEND_PROPERTY_SEED = 2026092201
SPEND_PROPERTY_EXAMPLES = 40
WALL_TIME_PROPERTY_SEED = 2026092202
WALL_TIME_PROPERTY_EXAMPLES = 40
DEDUPLICATION_PROPERTY_SEED = 2026092203
DEDUPLICATION_PROPERTY_EXAMPLES = 40
PROVENANCE_PROPERTY_SEED = 2026092204
PROVENANCE_PROPERTY_EXAMPLES = 40
INERT_BODY_PROPERTY_SEED = 2026092205
INERT_BODY_PROPERTY_EXAMPLES = 40
READ_CAUSE_PROPERTY_SEED = 2026092206
READ_CAUSE_PROPERTY_EXAMPLES = 30
ARGUMENT_PROPERTY_SEED = 2026092207
ARGUMENT_PROPERTY_EXAMPLES = 30
READ_CAUSE_MAPPING_SEED = 2026092208
READ_CAUSE_MAPPING_EXAMPLES = 20


class LedgerModule(Protocol):
    """Source-owned ledger contract exposed through the shipped module."""

    SCHEMA_VERSION: int
    SCHEMA_VERSION_FIELD: str
    CHANGE_FIELD: str
    MAIL_RECORDS_FIELD: str
    JOURNAL_RUNS_FIELD: str
    STATUS_FIELD: str
    DETAIL_FIELD: str
    LEDGER_FIELD: str
    FINDING_PROVENANCE_FIELD: str
    RUNNING_SPEND_FIELD: str
    WALL_TIME_SECONDS_FIELD: str
    PASSES_FIELD: str
    HEADS_FIELD: str
    VERDICTS_FIELD: str
    DECISIONS_FIELD: str
    FAILURES_FIELD: str
    READS_FIELD: str
    SUCCEEDED_STATUS: str
    INVALID_INPUT_STATUS: str
    DERIVE_OPERATION: str
    SUCCESS_EXIT_CODE: int
    INVALID_INPUT_EXIT_CODE: int
    BODY_FIELD: str
    ID_FIELD: str
    RUN_TOKEN_FIELD: str
    PASS_FIELD: str
    HEAD_FIELD: str
    VERDICT_FIELD: str
    DECISION_FIELD: str
    FAILURE_FIELD: str
    READ_FIELD: str
    SPEND_FIELD: str
    CURRENCY_FIELD: str
    AMOUNT_FIELD: str
    CAUSE_FIELD: str
    SOURCE_FIELD: str
    VALUE_FIELD: str
    SOURCE_KIND_FIELD: str
    SOURCE_ID_FIELD: str
    MAIL_SOURCE_KIND: str
    JOURNAL_SOURCE_KIND: str
    MAIL_POSITION_LABEL: str
    JOURNAL_POSITION_LABEL: str
    READ_CAUSES: frozenset[str]
    SCALAR_EVENT_COLLECTIONS: tuple[tuple[str, str], ...]
    COLLECTION_FIELDS: tuple[str, ...]

    def main(
        self,
        argv: Sequence[str] | None = None,
        *,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
    ) -> int: ...


@dataclass(frozen=True)
class LedgerEntrypointObservation:
    """Captured public entry-point output with its source contract."""

    exit_code: int
    result: dict[str, object]
    stderr: str


def load_ledger_module() -> LedgerModule:
    """Load the shipped ledger entry point from the authored skill surface."""
    specification = importlib.util.spec_from_file_location(
        LEDGER_MODULE_NAME, LEDGER_SCRIPT_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Cannot load ledger module: {LEDGER_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return cast(LedgerModule, module)


def run_ledger(
    arguments: Sequence[str], payload: Mapping[str, object] | str
) -> LedgerEntrypointObservation:
    """Execute the ledger entry point and capture its observations.

    The error stream is captured by redirecting the process's own `sys.stderr`
    for the duration of the call, so any write the entry point makes to the real
    stream reaches the observation.
    """
    module = load_ledger_module()
    standard_output = io.StringIO()
    standard_error = io.StringIO()
    standard_input = payload if isinstance(payload, str) else json.dumps(payload)
    with contextlib.redirect_stderr(standard_error):
        exit_code = module.main(
            arguments,
            stdin=io.StringIO(standard_input),
            stdout=standard_output,
        )
    return LedgerEntrypointObservation(
        exit_code=exit_code,
        result=cast(dict[str, object], json.loads(standard_output.getvalue())),
        stderr=standard_error.getvalue(),
    )


def ledger_body(module: LedgerModule, event: Mapping[str, object]) -> str:
    """Render one ledger event as the JSON body a mail record carries."""
    return json.dumps({module.LEDGER_FIELD: dict(event)})


def mail_record(module: LedgerModule, identifier: int, body: str) -> dict[str, object]:
    """One mail record carrying its store-assigned identity and raw body."""
    return {module.ID_FIELD: identifier, module.BODY_FIELD: body}


def event_record(
    module: LedgerModule, identifier: int, event: Mapping[str, object]
) -> dict[str, object]:
    """One mail record whose body carries the supplied ledger event."""
    return mail_record(module, identifier, ledger_body(module, event))


def journal_run(
    module: LedgerModule, run_token: str, event: Mapping[str, object]
) -> dict[str, object]:
    """One verification-journal run carrying its token and event fields."""
    return {module.RUN_TOKEN_FIELD: run_token, **dict(event)}


def derivation_document(
    module: LedgerModule,
    change: str,
    mail_records: Sequence[Mapping[str, object]],
    journal_runs: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """The versioned input document the derivation entry point accepts."""
    return {
        module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION,
        module.CHANGE_FIELD: change,
        module.MAIL_RECORDS_FIELD: list(mail_records),
        module.JOURNAL_RUNS_FIELD: list(journal_runs),
    }


def derive(
    module: LedgerModule,
    change: str,
    mail_records: Sequence[Mapping[str, object]] = (),
    journal_runs: Sequence[Mapping[str, object]] = (),
    arguments: Sequence[str] | None = None,
) -> LedgerEntrypointObservation:
    """Execute the entry point over one document and capture its observation."""
    vector = [module.DERIVE_OPERATION] if arguments is None else list(arguments)
    return run_ledger(
        vector, derivation_document(module, change, mail_records, journal_runs)
    )


def run_spend_property(
    assert_spend: Callable[
        [LedgerModule, dict[str, list[str]], LedgerEntrypointObservation], None
    ],
) -> None:
    """Drive generated per-currency spend; the linked test owns the total."""
    module = load_ledger_module()

    @seed(SPEND_PROPERTY_SEED)
    @settings(max_examples=SPEND_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(series=spend_series(), change=change_identifiers())
    def generated_spend(series: dict[str, list[str]], change: str) -> None:
        events = [
            (currency, amount)
            for currency, amounts in series.items()
            for amount in amounts
        ]
        records = [
            event_record(
                module,
                identifier,
                {
                    module.SPEND_FIELD: {
                        module.CURRENCY_FIELD: currency,
                        module.AMOUNT_FIELD: amount,
                    }
                },
            )
            for identifier, (currency, amount) in enumerate(events, start=1)
        ]
        assert_spend(module, series, derive(module, change, mail_records=records))

    run_replayable_property(
        generated_spend,
        seed_value=SPEND_PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )


def run_wall_time_property(
    assert_wall_time: Callable[
        [LedgerModule, list[str], LedgerEntrypointObservation], None
    ],
) -> None:
    """Drive generated durations across both sources; the test owns the total."""
    module = load_ledger_module()

    @seed(WALL_TIME_PROPERTY_SEED)
    @settings(max_examples=WALL_TIME_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(series=duration_series(), change=change_identifiers())
    def generated_wall_time(series: list[str], change: str) -> None:
        midpoint = len(series) // 2
        records = [
            event_record(module, index + 1, {module.WALL_TIME_SECONDS_FIELD: value})
            for index, value in enumerate(series[:midpoint])
        ]
        runs = [
            journal_run(module, f"run-{index}", {module.WALL_TIME_SECONDS_FIELD: value})
            for index, value in enumerate(series[midpoint:])
        ]
        assert_wall_time(module, series, derive(module, change, records, runs))

    run_replayable_property(
        generated_wall_time,
        seed_value=WALL_TIME_PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )


def run_deduplication_property(
    assert_deduplication: Callable[
        [
            LedgerModule,
            list[tuple[str, str]],
            Callable[[Sequence[tuple[str, str]]], LedgerEntrypointObservation],
        ],
        None,
    ],
) -> None:
    """Drive run series carrying repeated tokens; the test owns the dedup law."""
    module = load_ledger_module()

    @seed(DEDUPLICATION_PROPERTY_SEED)
    @settings(
        max_examples=DEDUPLICATION_PROPERTY_EXAMPLES, deadline=None, print_blob=True
    )
    @given(series=repeated_run_series(), change=change_identifiers())
    def generated_deduplication(series: list[tuple[str, str]], change: str) -> None:
        def derive_series(
            runs: Sequence[tuple[str, str]],
        ) -> LedgerEntrypointObservation:
            return derive(
                module,
                change,
                journal_runs=[
                    journal_run(module, token, {module.PASS_FIELD: label})
                    for token, label in runs
                ],
            )

        assert_deduplication(module, series, derive_series)

    run_replayable_property(
        generated_deduplication,
        seed_value=DEDUPLICATION_PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )


def run_provenance_property(
    assert_provenance: Callable[
        [
            LedgerModule,
            list[tuple[int, str]],
            list[tuple[str, str]],
            LedgerEntrypointObservation,
        ],
        None,
    ],
) -> None:
    """Drive distinct mail and journal carriers; the test owns the pairing."""
    module = load_ledger_module()

    @seed(PROVENANCE_PROPERTY_SEED)
    @settings(max_examples=PROVENANCE_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        mail=mail_carriers(), journal=journal_carriers(), change=change_identifiers()
    )
    def generated_provenance(
        mail: list[tuple[int, str]], journal: list[tuple[str, str]], change: str
    ) -> None:
        records = [
            event_record(module, identifier, {module.PASS_FIELD: label})
            for identifier, label in mail
        ]
        runs = [
            journal_run(module, token, {module.PASS_FIELD: label})
            for token, label in journal
        ]
        assert_provenance(module, mail, journal, derive(module, change, records, runs))

    run_replayable_property(
        generated_provenance,
        seed_value=PROVENANCE_PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )


def run_inert_body_property(
    assert_inert: Callable[
        [LedgerModule, LedgerEntrypointObservation, LedgerEntrypointObservation], None
    ],
) -> None:
    """Drive bodies that carry no ledger object beside an empty derivation."""
    module = load_ledger_module()

    @seed(INERT_BODY_PROPERTY_SEED)
    @settings(max_examples=INERT_BODY_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        bodies=st.lists(non_ledger_bodies(module), min_size=1, max_size=5),
        change=change_identifiers(),
    )
    def generated_inert(bodies: list[str], change: str) -> None:
        records = [
            mail_record(module, index + 1, body) for index, body in enumerate(bodies)
        ]
        assert_inert(
            module,
            derive(module, change, mail_records=records),
            derive(module, change),
        )

    run_replayable_property(
        generated_inert,
        seed_value=INERT_BODY_PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )


def run_foreign_read_cause_property(
    assert_refusal: Callable[[LedgerModule, int, LedgerEntrypointObservation], None],
) -> None:
    """Drive a read whose cause lies outside the declared set, at a known index."""
    module = load_ledger_module()

    @seed(READ_CAUSE_PROPERTY_SEED)
    @settings(max_examples=READ_CAUSE_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        cause=foreign_read_causes(module),
        details=read_details(),
        leading=leading_record_counts(),
        filler=pass_labels(),
        identifier=store_message_ids(),
        change=change_identifiers(),
    )
    def generated_read_cause(
        cause: object,
        details: dict[str, str],
        leading: int,
        filler: str,
        identifier: int,
        change: str,
    ) -> None:
        conforming = [
            event_record(module, index + 1, {module.PASS_FIELD: filler})
            for index in range(leading)
        ]
        offending = event_record(
            module,
            identifier,
            {module.READ_FIELD: {**details, module.CAUSE_FIELD: cause}},
        )
        assert_refusal(
            module,
            leading,
            derive(module, change, mail_records=[*conforming, offending]),
        )

    run_replayable_property(
        generated_read_cause,
        seed_value=READ_CAUSE_PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )


def run_foreign_argument_property(
    assert_refusal: Callable[
        [LedgerModule, list[str], LedgerEntrypointObservation], None
    ],
) -> None:
    """Drive argument vectors other than the declared derive vector."""
    module = load_ledger_module()

    @seed(ARGUMENT_PROPERTY_SEED)
    @settings(max_examples=ARGUMENT_PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(vector=foreign_argument_vectors(module), change=change_identifiers())
    def generated_arguments(vector: list[str], change: str) -> None:
        assert_refusal(module, vector, derive(module, change, arguments=vector))

    run_replayable_property(
        generated_arguments,
        seed_value=ARGUMENT_PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )


def run_read_cause_mapping(
    assert_causes: Callable[
        [
            LedgerModule,
            dict[str, dict[str, object]],
            int,
            dict[str, LedgerEntrypointObservation],
        ],
        None,
    ],
) -> None:
    """Drive every declared read cause; the test owns completeness and recording."""
    module = load_ledger_module()

    @seed(READ_CAUSE_MAPPING_SEED)
    @settings(max_examples=READ_CAUSE_MAPPING_EXAMPLES, deadline=None, print_blob=True)
    @given(
        details=read_details(),
        identifier=store_message_ids(),
        change=change_identifiers(),
    )
    def generated_causes(details: dict[str, str], identifier: int, change: str) -> None:
        reads: dict[str, dict[str, object]] = {
            cause: {**details, module.CAUSE_FIELD: cause}
            for cause in sorted(module.READ_CAUSES)
        }
        observations = {
            cause: derive(
                module,
                change,
                mail_records=[
                    event_record(module, identifier, {module.READ_FIELD: read})
                ],
            )
            for cause, read in reads.items()
        }
        assert_causes(module, reads, identifier, observations)

    run_replayable_property(
        generated_causes,
        seed_value=READ_CAUSE_MAPPING_SEED,
        replay_path=MAPPING_REPLAY_PATH,
    )

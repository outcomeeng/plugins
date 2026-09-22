"""Property evidence for the officer ledger's derivation invariants."""

from collections.abc import Callable, Sequence
from decimal import MAX_EMAX, MAX_PREC, MIN_EMIN, Decimal, localcontext
from typing import cast

from outcomeeng_testing.harnesses.officer_orchestration import (
    LedgerEntrypointObservation,
    LedgerModule,
    run_deduplication_property,
    run_exact_text_property,
    run_foreign_argument_property,
    run_foreign_read_cause_property,
    run_foreign_schema_version_property,
    run_inert_body_property,
    run_parser_refusal_property,
    run_provenance_property,
    run_repeated_value_property,
    run_spend_property,
    run_wall_time_property,
)


def test_a_body_carrying_no_ledger_object_contributes_nothing() -> None:
    """Records whose bodies carry no ledger object leave the ledger untouched."""

    def assert_inert(
        source: LedgerModule,
        populated: LedgerEntrypointObservation,
        empty: LedgerEntrypointObservation,
    ) -> None:
        assert populated.exit_code == source.SUCCESS_EXIT_CODE
        assert populated.stderr == ""
        assert populated.result == empty.result

    run_inert_body_property(assert_inert)


def test_running_spend_totals_each_currency_independently() -> None:
    """Each currency's total is the sum of that currency's amounts alone.

    The emitted total is compared as text against the exactly summed amounts,
    so a total that carries the right value at a coarser precision than the
    amounts it came from fails here rather than comparing numerically equal.
    The oracle sums under a context that rounds nothing: summed under the
    default context it would shorten the expectation by the same digits a
    derivation losing its exact context shortens, and witness neither.
    """

    def assert_spend(
        source: LedgerModule,
        series: dict[str, list[str]],
        observation: LedgerEntrypointObservation,
    ) -> None:
        ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])
        totals = cast(dict[str, object], ledger[source.RUNNING_SPEND_FIELD])

        assert observation.exit_code == source.SUCCESS_EXIT_CODE
        assert set(totals) == set(series)
        for currency, amounts in series.items():
            with localcontext(prec=MAX_PREC, Emax=MAX_EMAX, Emin=MIN_EMIN):
                unrounded = str(sum((Decimal(amount) for amount in amounts), Decimal()))
            assert totals[currency] == unrounded

    run_spend_property(assert_spend)


def test_wall_time_totals_every_event_duration() -> None:
    """Wall time is the sum of every duration across both derivation sources.

    The oracle sums under a context that rounds nothing, so a total the
    derivation shortened is not compared against an expectation shortened the
    same way.
    """

    def assert_wall_time(
        source: LedgerModule,
        series: list[str],
        observation: LedgerEntrypointObservation,
    ) -> None:
        ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])

        with localcontext(prec=MAX_PREC, Emax=MAX_EMAX, Emin=MIN_EMIN):
            unrounded = str(sum((Decimal(duration) for duration in series), Decimal()))

        assert observation.exit_code == source.SUCCESS_EXIT_CODE
        assert ledger[source.WALL_TIME_SECONDS_FIELD] == unrounded

    run_wall_time_property(assert_wall_time)


def test_every_total_is_emitted_as_exact_decimal_text() -> None:
    """Both totals reach the consumer as the exact decimal text of their value.

    A JSON number literal is read into a double by conformant parsers, so the
    emitted form is checked to be text and to carry every digit of the amount
    and duration the record supplied. The generated amounts and durations reach
    precisions the default decimal context rounds, and the oracle accumulates
    under a context that rounds nothing, so a derivation that accumulated in
    the default context emits fewer digits than this comparison expects.
    """

    def assert_exact_text(
        source: LedgerModule,
        payload: dict[str, str],
        observation: LedgerEntrypointObservation,
    ) -> None:
        ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])
        totals = cast(dict[str, object], ledger[source.RUNNING_SPEND_FIELD])
        spend = totals[payload["currency"]]
        duration = ledger[source.WALL_TIME_SECONDS_FIELD]

        with localcontext(prec=MAX_PREC, Emax=MAX_EMAX, Emin=MIN_EMIN):
            unrounded_spend = str(Decimal() + Decimal(payload["amount"]))
            unrounded_duration = str(Decimal() + Decimal(payload["duration"]))

        assert observation.exit_code == source.SUCCESS_EXIT_CODE
        assert isinstance(spend, str)
        assert isinstance(duration, str)
        assert spend == unrounded_spend
        assert duration == unrounded_duration

    run_exact_text_property(assert_exact_text)


def test_a_document_the_parser_refuses_becomes_the_invalid_input_result() -> None:
    """A source the JSON parser cannot read reaches the caller as a result.

    The parser refuses more than malformed syntax: an integer literal wider
    than the interpreter converts refuses a document whose every other byte is
    well formed. Each such refusal is the versioned result on stdout with an
    empty error stream, so one parse reads every outcome and no source shape
    reaches the caller as a traceback.
    """

    def assert_refusal(
        source: LedgerModule,
        observation: LedgerEntrypointObservation,
    ) -> None:
        detail = cast(str, observation.result[source.DETAIL_FIELD])

        assert observation.exit_code == source.INVALID_INPUT_EXIT_CODE
        assert observation.stderr == ""
        assert observation.result[source.STATUS_FIELD] == source.INVALID_INPUT_STATUS
        assert observation.result[source.SCHEMA_VERSION_FIELD] == source.SCHEMA_VERSION
        assert detail != ""

    run_parser_refusal_property(assert_refusal)


def test_repeated_source_identities_contribute_once() -> None:
    """Each source derives the ledger of its first occurrence per identity.

    Both sources are driven in one document, so a rule that admits a repeated
    mail record while rejecting a repeated run — or the reverse — fails here.
    """

    def assert_deduplication(
        source: LedgerModule,
        mail: list[tuple[int, dict[str, str]]],
        journal: list[tuple[str, dict[str, str]]],
        derive_series: Callable[
            [
                Sequence[tuple[int, dict[str, str]]],
                Sequence[tuple[str, dict[str, str]]],
            ],
            LedgerEntrypointObservation,
        ],
    ) -> None:
        first_records: list[tuple[int, dict[str, str]]] = []
        seen_ids: set[int] = set()
        for identifier, payload in mail:
            if identifier not in seen_ids:
                seen_ids.add(identifier)
                first_records.append((identifier, payload))
        first_runs: list[tuple[str, dict[str, str]]] = []
        seen_tokens: set[str] = set()
        for token, payload in journal:
            if token not in seen_tokens:
                seen_tokens.add(token)
                first_runs.append((token, payload))
        complete = derive_series(mail, journal)
        deduplicated = derive_series(first_records, first_runs)
        ledger = cast(dict[str, object], complete.result[source.LEDGER_FIELD])

        assert complete.exit_code == source.SUCCESS_EXIT_CODE
        assert complete.result == deduplicated.result
        assert len(cast(list[object], ledger[source.PASSES_FIELD])) == len(
            seen_ids
        ) + len(seen_tokens)

    run_deduplication_property(assert_deduplication)


def test_a_value_a_record_repeats_enters_its_collection_each_time() -> None:
    """A finding or read a record lists twice is recorded twice.

    Deduplication is a rule about a source record, not about a derived entry,
    so a collection that dropped a repeat would lose a value the record
    genuinely carried.
    """

    def assert_repeats(
        source: LedgerModule,
        finding: dict[str, str],
        read: dict[str, object],
        repeats: int,
        identifier: int,
        observation: LedgerEntrypointObservation,
    ) -> None:
        ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])
        provenance = {
            source.SOURCE_KIND_FIELD: source.MAIL_SOURCE_KIND,
            source.SOURCE_ID_FIELD: identifier,
        }

        assert observation.exit_code == source.SUCCESS_EXIT_CODE
        assert (
            ledger[source.FINDING_PROVENANCE_FIELD]
            == [{source.VALUE_FIELD: finding, source.SOURCE_FIELD: provenance}]
            * repeats
        )
        assert (
            ledger[source.READS_FIELD]
            == [{source.VALUE_FIELD: read, source.SOURCE_FIELD: provenance}] * repeats
        )

    run_repeated_value_property(assert_repeats)


def test_every_entry_carries_the_provenance_of_its_record() -> None:
    """Each entry names the mail identity or run token that carried it."""

    def assert_provenance(
        source: LedgerModule,
        mail: list[tuple[int, str]],
        journal: list[tuple[str, str]],
        observation: LedgerEntrypointObservation,
    ) -> None:
        ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])
        expected = [
            {
                source.VALUE_FIELD: label,
                source.SOURCE_FIELD: {
                    source.SOURCE_KIND_FIELD: source.MAIL_SOURCE_KIND,
                    source.SOURCE_ID_FIELD: identifier,
                },
            }
            for identifier, label in mail
        ] + [
            {
                source.VALUE_FIELD: label,
                source.SOURCE_FIELD: {
                    source.SOURCE_KIND_FIELD: source.JOURNAL_SOURCE_KIND,
                    source.SOURCE_ID_FIELD: token,
                },
            }
            for token, label in journal
        ]

        assert observation.exit_code == source.SUCCESS_EXIT_CODE
        assert ledger[source.PASSES_FIELD] == expected

    run_provenance_property(assert_provenance)


def test_a_read_cause_outside_the_declared_set_is_refused() -> None:
    """An undeclared cause refuses the document, naming causes and position."""

    def assert_refusal(
        source: LedgerModule,
        position: int,
        observation: LedgerEntrypointObservation,
    ) -> None:
        detail = cast(str, observation.result[source.DETAIL_FIELD])

        assert observation.exit_code == source.INVALID_INPUT_EXIT_CODE
        assert observation.stderr == ""
        assert observation.result[source.STATUS_FIELD] == source.INVALID_INPUT_STATUS
        assert f"{source.MAIL_POSITION_LABEL} {position}" in detail
        for cause in source.READ_CAUSES:
            assert cause in detail

    run_foreign_read_cause_property(assert_refusal)


def test_a_schema_version_other_than_the_declared_one_is_refused() -> None:
    """Only the declared integer admits a document as a supported version.

    `True` equals `1` and so does `1.0`, so a gate comparing values alone
    admits a boolean and a float as the declared version and stamps the result
    with a version the document never carried. The refusal names the version
    the entry point requires.
    """

    def assert_refusal(
        source: LedgerModule,
        observation: LedgerEntrypointObservation,
    ) -> None:
        detail = cast(str, observation.result[source.DETAIL_FIELD])

        assert observation.exit_code == source.INVALID_INPUT_EXIT_CODE
        assert observation.stderr == ""
        assert observation.result[source.STATUS_FIELD] == source.INVALID_INPUT_STATUS
        assert source.SCHEMA_VERSION_FIELD in detail
        assert str(source.SCHEMA_VERSION) in detail

    run_foreign_schema_version_property(assert_refusal)


def test_an_argument_vector_other_than_derive_is_refused() -> None:
    """Any other argument vector refuses, naming the required and received one."""

    def assert_refusal(
        source: LedgerModule,
        vector: list[str],
        observation: LedgerEntrypointObservation,
    ) -> None:
        detail = cast(str, observation.result[source.DETAIL_FIELD])

        assert observation.exit_code == source.INVALID_INPUT_EXIT_CODE
        assert observation.stderr == ""
        assert observation.result[source.STATUS_FIELD] == source.INVALID_INPUT_STATUS
        assert source.DERIVE_OPERATION in detail
        for token in vector:
            assert token in detail

    run_foreign_argument_property(assert_refusal)

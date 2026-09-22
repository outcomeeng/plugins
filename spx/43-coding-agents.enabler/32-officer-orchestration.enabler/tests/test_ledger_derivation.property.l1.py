"""Property evidence for the officer ledger's derivation invariants."""

from collections.abc import Callable, Sequence
from decimal import Decimal
from typing import cast

from outcomeeng_testing.harnesses.officer_orchestration import (
    LedgerEntrypointObservation,
    LedgerModule,
    run_deduplication_property,
    run_foreign_argument_property,
    run_foreign_read_cause_property,
    run_inert_body_property,
    run_provenance_property,
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
    """Each currency's total is the sum of that currency's amounts alone."""

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
            assert Decimal(str(totals[currency])) == sum(
                (Decimal(amount) for amount in amounts), Decimal()
            )

    run_spend_property(assert_spend)


def test_wall_time_totals_every_event_duration() -> None:
    """Wall time is the sum of every duration across both derivation sources."""

    def assert_wall_time(
        source: LedgerModule,
        series: list[str],
        observation: LedgerEntrypointObservation,
    ) -> None:
        ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])

        assert observation.exit_code == source.SUCCESS_EXIT_CODE
        assert Decimal(str(ledger[source.WALL_TIME_SECONDS_FIELD])) == sum(
            (Decimal(duration) for duration in series), Decimal()
        )

    run_wall_time_property(assert_wall_time)


def test_repeated_run_tokens_contribute_once() -> None:
    """A run series derives the ledger of its first occurrence per token."""

    def assert_deduplication(
        source: LedgerModule,
        series: list[tuple[str, str]],
        derive_series: Callable[
            [Sequence[tuple[str, str]]], LedgerEntrypointObservation
        ],
    ) -> None:
        first_occurrences: list[tuple[str, str]] = []
        seen: set[str] = set()
        for token, label in series:
            if token not in seen:
                seen.add(token)
                first_occurrences.append((token, label))
        complete = derive_series(series)
        deduplicated = derive_series(first_occurrences)
        ledger = cast(dict[str, object], complete.result[source.LEDGER_FIELD])

        assert complete.exit_code == source.SUCCESS_EXIT_CODE
        assert complete.result == deduplicated.result
        assert len(cast(list[object], ledger[source.PASSES_FIELD])) == len(seen)

    run_deduplication_property(assert_deduplication)


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

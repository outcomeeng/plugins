"""Mapping evidence over the officer ledger's declared read-cause domain."""

from typing import cast

from outcomeeng_testing.harnesses.officer_orchestration import (
    LedgerEntrypointObservation,
    LedgerModule,
    run_read_cause_mapping,
)


def test_every_declared_read_cause_records_one_read() -> None:
    """Each declared cause maps to one recorded read carrying its payload."""

    def assert_causes(
        source: LedgerModule,
        reads: dict[str, dict[str, object]],
        identifier: int,
        observations: dict[str, LedgerEntrypointObservation],
    ) -> None:
        provenance = {
            source.SOURCE_KIND_FIELD: source.MAIL_SOURCE_KIND,
            source.SOURCE_ID_FIELD: identifier,
        }

        for cause in sorted(source.READ_CAUSES):
            observation = observations[cause]
            ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])

            assert observation.exit_code == source.SUCCESS_EXIT_CODE
            assert observation.stderr == ""
            assert ledger[source.READS_FIELD] == [
                {source.VALUE_FIELD: reads[cause], source.SOURCE_FIELD: provenance}
            ]

    run_read_cause_mapping(assert_causes)

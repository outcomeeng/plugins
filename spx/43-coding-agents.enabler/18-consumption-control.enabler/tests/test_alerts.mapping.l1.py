"""The recorded alert read maps stored records after an instant to identity, instant, and signal."""

from outcomeeng_testing.harnesses.consumption_control import (
    AlertReadObservation,
    alert_read_property,
    unreadable_alert_observations,
)


def test_records_after_instant_map_oldest_first() -> None:
    def check(observed: AlertReadObservation) -> None:
        later = sorted(
            (record for record in observed.stored if record[1] > observed.cutoff),
            key=lambda record: (record[1], record[0]),
        )
        assert observed.result[observed.fields.STATUS] == observed.statuses.READ
        assert observed.result[observed.fields.ROOT] == str(observed.root)
        assert observed.result[observed.fields.RECORDS] == [
            {
                observed.fields.IDENTITY: identity,
                observed.fields.RECORDED_UTC: stamp,
                observed.fields.SIGNAL: signal,
            }
            for identity, _, stamp, signal in later
        ]

    alert_read_property(check)


def test_read_changes_no_stored_record_or_journal_entry() -> None:
    def check(observed: AlertReadObservation) -> None:
        assert observed.state_after == observed.state_before
        assert observed.journal_after == b""

    alert_read_property(check)


def test_unreadable_state_names_root_without_records() -> None:
    for observed in unreadable_alert_observations():
        assert observed.result[observed.fields.STATUS] == observed.statuses.UNREADABLE
        assert observed.result[observed.fields.ROOT] == str(observed.root)
        assert observed.fields.RECORDS not in observed.result
        assert observed.state_after == observed.state_before

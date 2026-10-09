"""Frozen report formats reconcile with bounded linked native evidence."""

from outcomeeng_testing.harnesses.consumption_control import (
    report_observation,
    workspace,
)


def test_formats_and_excerpt_links_share_measurement() -> None:
    with workspace() as work:
        observed = report_observation(work)
        assert observed.headline_values == observed.expected_headline_values
        assert all(
            row in observed.html_rows[section]
            for section, rows in observed.expected_rows.items()
            for row in rows
        )
        assert not observed.verified_outputs
        assert observed.unknown_output_text in observed.document
        assert observed.json_usage == observed.measured_usage == observed.csv_usage
        assert observed.links
        assert all(link in observed.document for link in observed.links)
        assert observed.retained_excerpt_size <= observed.excerpt_bound
        assert observed.unknown_conversion is None
        assert not observed.temporary_files

"""Frozen report formats reconcile with bounded linked native evidence."""

from outcomeeng_testing.harnesses.consumption_control import (
    report_observation,
    workspace,
)


def test_formats_and_excerpt_links_share_measurement() -> None:
    with workspace() as work:
        observed = report_observation(work)
        assert observed.headline_values == (
            observed.display(
                observed.measurement[observed.fields.API_EQUIVALENT_USD],
                observed.formats.SUMMARY_COST,
            ),
            observed.display(
                observed.measurement[observed.fields.REQUESTS], observed.formats.COUNT
            ),
            observed.display(
                observed.measurement[observed.fields.CHILD_REQUESTS],
                observed.formats.COUNT,
            ),
            str(len(observed.measurement[observed.fields.GAPS])),
        )
        assert all(
            (
                name,
                str(group[observed.fields.REQUESTS]),
                observed.display(
                    group[observed.fields.API_EQUIVALENT_USD], observed.formats.COST
                ),
                observed.display(
                    group[observed.fields.SHARE_MEASURED_COST], observed.formats.SHARE
                ),
            )
            in observed.html_rows[observed.sections.CONSUMPTION]
            for name, group in observed.measurement[observed.fields.MODELS].items()
        )
        assert all(
            (
                name,
                group[observed.fields.FIRST_UTC],
                str(group[observed.fields.DURATION_SECONDS]),
                group[observed.fields.MODEL],
                str(group[observed.fields.REQUESTS]),
                *(str(group[key]) for key in observed.token_keys),
                observed.display(
                    group[observed.fields.API_EQUIVALENT_USD], observed.formats.COST
                ),
                observed.display(
                    group[observed.fields.SHARE_MEASURED_COST], observed.formats.SHARE
                ),
            )
            in observed.html_rows[observed.sections.CONSUMPTION]
            for name, group in observed.measurement[observed.fields.SESSIONS].items()
        )
        assert all(
            (
                name,
                observed.display(
                    group[observed.fields.EARLY_CONTEXT_MEAN], observed.formats.CONTEXT
                ),
                observed.display(
                    group[observed.fields.LATE_CONTEXT_MEAN], observed.formats.CONTEXT
                ),
                observed.display(
                    group[observed.fields.CONTEXT_GROWTH_RATIO], observed.formats.GROWTH
                ),
                observed.display(
                    group[observed.fields.EARLY_COST_MEAN],
                    observed.formats.REQUEST_COST,
                ),
                observed.display(
                    group[observed.fields.LATE_COST_MEAN], observed.formats.REQUEST_COST
                ),
            )
            in observed.html_rows[observed.sections.CONTEXT]
            for name, group in observed.measurement[observed.fields.SESSIONS].items()
        )
        assert all(
            (
                key,
                str(observed.measurement[key]),
                observed.display(
                    observed.measurement[observed.fields.COST_COMPONENTS][key],
                    observed.formats.COST,
                ),
            )
            in observed.html_rows[observed.sections.CACHE]
            for key in observed.token_keys
        )
        assert not observed.verified_outputs
        assert observed.unknown_output_text in observed.document
        assert observed.json_usage == observed.measured_usage == observed.csv_usage
        assert observed.links
        assert all(link in observed.document for link in observed.links)
        assert observed.retained_excerpt_size <= observed.excerpt_bound
        assert observed.unknown_conversion is None
        assert not observed.temporary_files

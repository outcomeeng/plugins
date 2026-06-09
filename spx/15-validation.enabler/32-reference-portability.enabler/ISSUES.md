# Issues: Reference Portability Validation

## CLI report/exit behaviors lack scenario assertions (FOLLOW-UP)

`tests/test_reference_portability.compliance.l1.py` exercises two scenario-level
behaviors of the validator's CLI surface — `test_cli_names_file_and_line_and_exits_nonzero`
and `test_cli_portable_content_exits_zero` — that no spec assertion declares. The
sibling `spx/15-validation.enabler/32-skill-injection-safety.enabler` carries a
Scenarios section for the equivalent report/exit behaviors.

**Resolution shape**: add a Scenarios section to `reference-portability.md` declaring
(1) a file containing a non-portable reference is reported with path, line, and
reference and exits non-zero; (2) a file whose references are all portable exits zero.
Move the two CLI tests into `tests/test_reference_portability.scenario.l1.py` so one
assertion type lives per file. Surfaced by the local `reviewing-changes` gate
(2026-06-09).

## Sample inputs stay test-owned domain members, not source exports (resolved by decision)

A review pass proposed exporting canonical sample references from
`outcomeeng/validation/reference_portability.py` for the test to import. This is
declined: the detector's discriminator is a structural partition (numeric-prefix and
repository-segment shape), not a single source-owned constant, so the per-category
sample strings are domain members the test legitimately owns. Exporting sample data
from the source module purely for the test is the test-data-in-source anti-pattern
`spx/15-test-infrastructure.pdr.md` forbids, and the test-evidence audit approved the
inline samples on that basis.

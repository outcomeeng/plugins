# ISSUES — skill reference enabler

Coordination note; not spec truth.

## Placeholder report is not checked for the unmatched expansion `spx/15-validation.enabler/32-skill-reference.enabler/tests/test_skill_reference.scenario.l1.py` `test_unmatched_placeholder_and_alternation_member_report_expansion` `misaligned`

The assertion requires the unmatched-placeholder report to carry the unmatched expansion, but the test checks the expansion only on the alternation report and only file, line, and reference on the placeholder report.

**Settlement condition**: The test asserts the unmatched expansion on the placeholder report.

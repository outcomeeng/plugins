# ISSUES — grant locality

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## DEBT [evidence]: the grant-locality compliance test rebuilds the frontmatter boundary instead of driving the validator `spx/15-validation.enabler/32-grant-locality.enabler/tests/test_grant_locality.compliance.l1.py`, `test_escaping_grant_outside_the_frontmatter_is_not_a_violation`, `partial-coupling`

Defect class: `falsifiability`, rule `partial-coupling`.

Finding: `test_escaping_grant_outside_the_frontmatter_is_not_a_violation` at `spx/15-validation.enabler/32-grant-locality.enabler/tests/test_grant_locality.compliance.l1.py:29` backs the assertion that the validator reads grants only from an `allowed-tools` field declaration inside the file's opening frontmatter, so a skill body that quotes or documents an escaping grant, including at column zero, is not itself a violation. The test composes `find_escaping_grants(frontmatter(content))` itself instead of driving `scan_file` or `main`, so a mutation that removes the `frontmatter()` call from `scan_file` survives in this test. Only the scenario test over `observe_local_skill_files` catches that mutation. The harness function `observe_body_mention_files` drives the real command over the same body-mention files and no test consumes it.

Remediation target: the test file. The test drives the real command over the body-mention files through `observe_body_mention_files` and asserts that no violation is reported.

Settlement condition: removing the `frontmatter()` call from `scan_file` fails the compliance test, and `observe_body_mention_files` has a consuming test.

# ISSUES — skill frontmatter enabler

Coordination note; not spec truth.

## Name-format scenario asserts the offending name rather than the format rule `spx/15-validation.enabler/32-skill-frontmatter.enabler/tests/test_skill_frontmatter.scenario.l1.py` `test_bad_name_format_produces_error` `misaligned`

The assertion requires an error that references the name format rule, but the test checks only that the offending name appears in the message, so any name-related error passes.

**Settlement condition**: The test asserts that the reported error references the name format rule.

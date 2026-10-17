# ISSUES — execution policy enabler

Coordination note; not spec truth.

## DEBT [evidence]: expected tables repeat the converter's tables (f-001, f-002)

Two findings (both REJECT, oracle independence) in
`outcomeeng_testing/harnesses/agent_conversion.py`, read by the tests under
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-execution-policy.enabler/tests`:

- f-001 at line 75: `EXPECTED_PERMISSION_MODE_CORRESPONDENCE` is a
  hand-written table that repeats `PERMISSION_MODE_MAPPINGS` row for row
  (`default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`).
  The spec declares no rows and no captured reference backs the pairs.
- f-002 at line 86: `EXPECTED_TOOL_CLASSIFICATION` equals
  `READ_ONLY_TOOLS | SCRIPT_CAPABLE_TOOLS | WEB_CAPABLE_TOOLS | WRITE_CAPABLE_TOOLS`,
  and `test_tool_classification_matches_the_hand_authored_correspondence`
  compares one author-owned copy to the other.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run
token; the other entries below refer to this audit and this head.

The sibling native-artifact node records harness-owned expected tables as a
warning in
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-native-artifact.enabler/ISSUES.md`.

**Resolution shape**: the spec declares the tool classes and the
`permissionMode` rows, and one audit assertion holds the converter's constants
to that declaration. The mapping tests take class membership and rows by
importing `READ_ONLY_TOOLS`, `SCRIPT_CAPABLE_TOOLS`, `WEB_CAPABLE_TOOLS`,
`WRITE_CAPABLE_TOOLS`, and `PERMISSION_MODE_MAPPINGS` from the converter, and
the harness tables `EXPECTED_PERMISSION_MODE_CORRESPONDENCE` and
`EXPECTED_TOOL_CLASSIFICATION` and the test that compares them are removed.

**Evidence that the text lies outside the change.** `git diff -U0
origin/main...HEAD` reports no hunk in the cited tests,
`outcomeeng_testing/harnesses/agent_conversion.py`, or
`outcomeeng/distribution/agents.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset only adds symbols to
`outcomeeng/distribution/profiles.py` (model prices and usage token classes),
and no symbol the cited tests import is renamed or altered. It also narrows the
configuration guard in `outcomeeng/validation/profile_configuration.py`, which
agent conversion does not call.

**Settlement condition**: neither expected table exists in the harness or the
tests; the declaration in the spec is the only second statement of the values.

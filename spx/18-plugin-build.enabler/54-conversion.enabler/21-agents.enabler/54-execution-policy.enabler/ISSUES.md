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

**Resolution shape**: derive the rows from an independently owned source, or
declare them in the spec.

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

**Settlement condition**: neither expected table repeats the converter's table;
each is derived from an independently owned source or declared in the spec.

## DEBT [evidence]: web-capability mapping exercised only over whole class sets (f-003)

Finding f-003 (REJECT, incomplete mapping domain) at
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-execution-policy.enabler/tests/test_execution_policy.mapping.l1.py:60`:
only whole class sets are exercised. The "any web-capable tool" quantifier and
the "omits web-capable tools" branch are never tested with a single or mixed
tool set, so mutating `map_web_search` or `infer_sandbox_mode` to a superset
test passes.

The audit and head are those of the first entry above; the verdict carries no
sealed run token.

**Resolution shape**: enumerate mixed and single-tool allowlists.

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

**Settlement condition**: the mapping test covers single-tool and mixed
allowlists, so a superset mutation of `map_web_search` or `infer_sandbox_mode`
fails it.

## DEBT [evidence]: converted `web_search` unobserved (f-004)

Finding f-004 (REJECT, surviving mutation) at
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-execution-policy.enabler/tests/test_execution_policy.mapping.l1.py:48`:
no test reads `web_search` from `convert_agent` output. Deleting
`values["web_search"] = web_search` in `outcomeeng/distribution/agents.py`
(lines 270-272) fails no test.

The audit and head are those of the first entry above; the verdict carries no
sealed run token.

**Resolution shape**: assert `web_search` on converted output.

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

**Settlement condition**: a test asserts `web_search` on `convert_agent`
output, so deleting the assignment fails it.

## DEBT [evidence]: tool-derived read-only sandbox fallback unobserved (f-005)

Finding f-005 (REJECT, surviving mutation) at
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/54-execution-policy.enabler/tests/test_execution_policy.mapping.l1.py:68`:
tool-derived read-only sandbox inference is tested only through
`infer_sandbox_mode`. Deleting the fallback in `convert_agent`
(`outcomeeng/distribution/agents.py` lines 259-267) fails no test.

The audit and head are those of the first entry above; the verdict carries no
sealed run token.

**Resolution shape**: assert `sandbox_mode` on converted output.

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

**Settlement condition**: a test asserts `sandbox_mode` on `convert_agent`
output for a read-only tool allowlist, so deleting the fallback fails it.

# ISSUES — coding agents

Known imperfections in the coding-agents subtree that no single changeset settles. Each entry names the files, the rule they strain, the evidence, and the condition under which the entry closes.

## Compliance scanners ship inside the environment adapters

A shipped environment adapter carries the regex tables and the scanner functions that detect a sibling script constructing its tool's raw command or invoking its help, and each node's compliance test is their only caller. The Prowl adapter, `src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py`, carries `RAW_PROWL_COMMAND_PATTERNS` (line 410) and `raw_prowl_command_violations` (line 788). The herdr and agent-mail adapters that `spx/43-coding-agents.enabler/18-herdr-environment.enabler` and `spx/43-coding-agents.enabler/18-agent-mail.enabler` specify carry the same shape in the changeset that ships them, `work/change-88-slice-1`: `RAW_HERDR_COMMAND_PATTERNS`, `HERDR_HELP_PATTERNS`, `raw_herdr_command_violations`, `herdr_help_violations` in `operate-herdr/scripts/herdr_environment.py`, and `RAW_MAIL_COMMAND_PATTERNS`, `GIT_PROJECT_KEY_PATTERNS`, `raw_mail_command_violations`, `git_project_key_violations` in `operate-agent-mail/scripts/agent_mail.py`. The artifact installed into consumer repositories therefore carries enforcement logic outside the responsibilities its adapter decision names: command grammar, response validation, error-code projection, record mapping, and bounds.

**Evidence.** `spec-tree:implementation-auditor` run `2026-09-18_11-13-57-525-5814472b13d4` over `67e7f9469938d1273ae14232dc6e560fc8e51368..3f2e301b1c4dc235dca84f3d34726263a9c14691` on `work/change-88-slice-1`, findings `single-responsibility` (severity `debt`) on the herdr and agent-mail adapters; the Prowl adapter shows the same shape on `main`.

**Gap.** Where the scanners live is a placement decision the adapter decisions do not make: the product's test infrastructure under `outcomeeng_testing/harnesses/`, or a repository-side checker the gate runs. The patterns declare what a raw command looks like for each tool; the compliance tests read them by import.

**Settlement condition.** The adapter decisions, or the environments decision above them, name one home for raw-command detection outside the shipped adapters; each node's compliance test imports the scanners and patterns from that home; and no shipped adapter under `src/plugins/coding-agents/` defines a scanner over sibling scripts.

**Second reading, same placement.** An isolated test-evidence audit reached the same constants from the other direction: the scanners and their patterns have no production consumer at all. The adapter's CLI exposes only `run` and `project-key`, `main` dispatches only those two, the skill instructs only those two invocations, and the script ships standalone with no entry point or export declaration, so the sole caller in the checkout is the node's compliance test. The enforcement rule the compliance assertion claims therefore lives in a constant only the tests read, which is the consumer check the second entry in this file names. Both readings settle together under the condition above.

**Evidence, second reading.** `spec-tree:test-evidence-auditor` finding `f-002` on head `d6d1b5458af190ac9d1f05775c869c08ab206c95`, rule `source-ownership`.

**The detector is also asymmetric, and relocation closes both.** `GIT_PROJECT_KEY_PATTERNS` matches only literal Git constructions: a quoted `git` opening a bracketed sequence, a quoted `.git` path segment, and shell text. Its sibling `RAW_MAIL_COMMAND_PATTERNS` additionally matches the bare constant name. A sibling script that names its Git vector through constants therefore passes a rule the adapter decision states as universal over shipped coding-agents Python scripts — and the agent-mail adapter now demonstrates exactly that spelling, since it assembles `PUBLIC_GIT_COMMON_DIR_COMMAND` from `GIT_COMMAND` and `REV_PARSE_COMMAND` rather than from literals.

Extending the pattern where it stands was attempted and withdrawn: adding an alternative deepens the coupling this entry records, because the constants have no production consumer and the compliance test is their only caller, so the extension enlarges a declaration only the tests read. The asymmetry settles with the relocation, not before it.

**Settlement condition, extended.** The home the condition above names carries a detector whose construction-form coverage is the same for every tool it guards, so a vector spelled through constants is detected wherever a vector spelled literally is.

**Evidence, third reading.** `spec-tree:implementation-auditor` run `2026-09-21_22-51-31-594-7659622868e9` on head `18903ace30be971b041eba9e74606e97bf0182ae`: `source-ownership` at `blocking` on the compliance test and `single-responsibility` at `debt` on the adapter, both naming the pattern extension as enlarging the declaration; and run `2026-09-21_22-18-07-162-b29e7184d5a1` on head `d6d1b5458af190ac9d1f05775c869c08ab206c95`, `adr-compliance-guard-asymmetry` at `debt`, which named the gap.

**Evidence, fourth reading.** `spec-tree:test-evidence-auditor` finding `f-001` on head `7ad28895500e40c4c106c1c510a175a6b52ddda9`, rule `source-ownership`: the herdr compliance test imports `raw_herdr_command_violations`, `herdr_help_violations`, `RAW_HERDR_COMMAND_PATTERNS`, and `HERDR_HELP_PATTERNS` from `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py`, and no production path consumes them.
**Evidence, fourth reading.** `instructions:skill-auditor` finding `f-012` against `src/plugins/coding-agents/skills/operate-herdr` on head `7ad28895500e40c4c106c1c510a175a6b52ddda9`, rule `conciseness_shipped_script`: the shipped script carries `participant_for`, `IDENTITY_AMBIGUOUS`, and the scanner helpers the run path never calls.
**Evidence, fifth reading.** `spec-tree:test-evidence-auditor` finding `f-003` on head `0caf8237bd062fa3d42b2e2a1e3441b8534ae1b8`, rule `source-ownership`: `participant_for` and `ExecutionStatus.IDENTITY_AMBIGUOUS` in `src/plugins/coding-agents/skills/operate-herdr/scripts/herdr_environment.py` are reached only by tests.

## The evidence-repair same-class scan stops at the test file

The apply flow's evidence repair scans for the rejected class inside the linked tests — a restated literal, a copied table — and stops there. The mirror shape is invisible to that scan: a value the tests import from production that no production path consumes. `agent_message.py` carried `FORBIDDEN_TARGET_FIELDS`, `FORBIDDEN_EXECUTABLE_FIELDS`, and `CLEAN_STATUS` as constants only the node's tests and harness read, so a test that iterated them was coupled to an inert declaration, and emptying the constant left the test green.

**Evidence.** `spec-tree:test-evidence-auditor` on `spx/43-coding-agents.enabler/21-agent-communication.enabler` at `1b2479a84f70e528315aa7fb16c40448d31817bf` rejected restated literals in the tests; the repair at `4113d674c47ccd118de35b522d4c626a96c17a52` closed those, and the second pass at that head rejected the relocated-constant shape under the same rule, `source-ownership`.
**Evidence.** The round-2 test-evidence audit on commit `c3980a80630789666e2186801fd8c10ecc856e45` again rejected source-owned values with no production consumer in Verifier session `/root/audit_officer_test_evidence_round2`.
**Evidence.** The third-round test-evidence audit on commit `5b2b3c35195a757864fb2396553a11f0a37450e3` again rejected the same `source-ownership` class after the widened repair, alternating back to restated production vocabulary and a test-invented Change identifier. The orchestrating session disposed the verdict as advisory because the node declares `malleability: spec`; this entry records the rule collision.
**Evidence.** PR #595 current-head CI review at `4dc9f6e7f7ad9a818752a4d6a078bfe4d5edaff2`, comment `issuecomment-5751528132`, raised the missing non-empty mail/journal scenario coverage. The orchestrating session disposed it as tracked/advisory because this node declares `malleability: spec` and Passing requires Validate, reachability, and tagged results, leaving evidence depth to the hardening Change.

**Gap.** `src/plugins/spec-tree/skills/apply/SKILL.md` `<stabilized_diff_rule>` names the same-class sweep over the touched node's governed files but does not name the consumer check: for every source-owned value a test imports, a production path consumes it.

**Settlement condition.** The apply flow's same-class sweep, or the test-evidence standard it applies, states that a source-owned value a test imports has a production consumer, and a compliance test's violating cases come from the linked test or a real production contract, never from a constant only tests read.

## An adapter skill description hedges its NEVER clause

`/agent-prompt-standards` `<constraint_language>` reads a NEVER as unconditional. `src/plugins/coding-agents/skills/operate-prowl/SKILL.md` line 4 ends its description's NEVER with "when this capability is available" — a condition that holds wherever the description is loaded, so it hedges the prohibition without narrowing it and spends characters from the shared listing budget on a no-op qualifier. The sibling descriptions of `operate-agent-mail` and `operate-herdr` end their NEVER at the prohibition.

**Impact**: a workflow reading the description can take the prohibition as conditional on some availability check it is expected to make, when no such check exists.

**Settlement condition**: the description ends its NEVER clause at the prohibition, and the skill surface of `spx/43-coding-agents.enabler/18-prowl-environment.enabler` passes the typed skill auditor.

**Why separate**: the instance belongs to `spx/43-coding-agents.enabler/18-prowl-environment.enabler`, whose skill surface carries its own audit gate and plugin bump.

**Evidence**: `instructions:skill-auditor` finding `f-007`, rule `hedged_never_clause`, against the agent-mail skill surface committed at `5f61aa80ce127256f1829e96535f33a1a0295227`, then a sweep over `src/plugins/*/skills/*/SKILL.md` that found the same clause in the herdr and Prowl sibling descriptions and no others.

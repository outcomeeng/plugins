# ISSUES — native agent recovery

Coordination note; not spec truth.

## DEBT [evidence]: this node's linked tests hold every predicate in their harness

`test-evidence-auditor` raised fifteen blocking findings, one per `[test]`-tagged assertion on this
node, all of a single class. Each of the three linked test files is
a single `assert <harness function>() == []` call, so no behavioral predicate is lexically visible in
any executed test: `tests/test_native_agent_recovery.mapping.l1.py` delegates to
`verify_native_agent_recovery_mappings`, `tests/test_native_agent_recovery.compliance.l1.py` to
`verify_native_agent_recovery_compliance`, and `tests/test_native_agent_recovery.property.l1.py` to
`verify_native_agent_recovery_properties`. All three live in
`outcomeeng_testing/harnesses/native_agent_recovery.py`, where every pass/fail comparison is computed
and aggregated into a returned failure list — including the two Hypothesis inner callbacks, whose
invariants append to an outer list rather than calling an assertion API.

[`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md)
governs the opposite arrangement: the linked executed test owns every behavioral predicate and
assertion API call, while a harness exposes observations and never returns a verdict. A function that
returns a failure list is a verdict-shaped helper, so a mutation to any governed rule is caught by
editing the harness rather than the test that claims to verify it.

**Resolution shape**: give each assertion an observation helper that returns the observed value beside
its independently derived expectation, then move every comparison into its own test function in the
linked file. The oracle independence the harness already supplies through its generators is preserved
by the inversion — the harness keeps producing the independent expectation and stops rendering the
verdict.

**Revisit condition**: the pattern spans several nodes rather than this one, so the inversion is one
migration with a shared harness contract rather than a per-node repair. This node's three files are
among the spec test files whose every assertion is a bare comparison of a harness return value against
an empty failure list; a wider set delegates to `assert_*` helpers in the same way.
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/ISSUES.md` tracks the same class
for its own node. Schedule the two together as that migration.

**Deferral reason**: the changeset that surfaced this widens one return annotation in the harness so
its declared type matches the type its single consumer already declares, unblocking a type check that
was failing for every branch. The auditor confirmed the widening is annotation-only and weakens no
assertion. Inverting an eight-hundred-line harness and fifteen assertions to land that one line would
replace a bounded repair with the first unit of a migration the other two nodes defer by the same
reasoning.

## DEBT [skill]: `recover-prowl-agents` mixes two forms of naming the composed skill

In `src/plugins/coding-agents/skills/recover-prowl-agents/SKILL.md`, lines 16, 62-67, and 131 name the
composed skill by the instruction "Use skill `coding-agents:operate-prowl`". Lines 45, 75, 90, 95, 97,
98, 101, 103, 105, and 175 name it by the bare mention `/operate-prowl`. The file therefore carries
both forms.

The `composed_dependency_form` rule, raised by `instructions:skill-auditor` in run
2026-10-10_18-51-24-026-b6f920c23fc3 at head ae83882a1cab0ee81bbab00b7fd538a75bf717bc, expects every
instruction that uses the dependency to state "Use skill `coding-agents:operate-prowl`".

**Settlement condition**: every mention of the composed skill in that file that instructs its use is
the instruction "Use skill `coding-agents:operate-prowl`", and a rerun of the skill auditor raises no
`composed_dependency_form` finding on the file.

## DEBT [consistency]: a `writableRoots` key naming no prepared candidate's worktree is dropped without an error

The CI review of https://github.com/outcomeeng/plugins/pull/689 at head
34741a48b95b26555c5217e122862026dceccb5e raised this finding at
`src/plugins/coding-agents/skills/recover-prowl-agents/scripts/recover_agents.py:1101`
(https://github.com/outcomeeng/plugins/pull/689#issuecomment-6244343208).

**Evidence**: the launch loop builds each delivery with `writable_roots.get(candidate.worktree_path, ())`.
A `writableRoots` key that names a stale or mistyped worktree path matches no launching candidate, so
recovery drops its roots and reports no error. Every other worktree- or pane-keyed identity check in
the file raises `AdapterError` with status `INVALID_TARGET` on a mismatch. No test in
`tests/test_native_agent_recovery.mapping.l1.py` or `tests/test_native_agent_recovery.compliance.l1.py`
supplies a key that matches no candidate, and the harness's `observe_writable_root_recovery` keys its
request roots only by worktrees the roster's candidates hold.

**Resolution shape**: reject a recover request whose `writableRoots` names a worktree held by no
prepared candidate, with the `INVALID_TARGET` status, before any binding, activation, or native launch,
and cover it with a compliance test that supplies several unprepared key forms.

**Deferral reason**: the fix needs a decision line and a spec assertion that
outcomeeng/changes#593's record does not state. The exact-native-recovery decision changes only through
a Change's Governance mutations, and the node's spec assertion has no decision to trace to. A Proposed
follow-up Change will state the decision line and the assertion, and carries the fix.

**Settlement condition**: a recover request whose `writableRoots` names a worktree held by no prepared
candidate ends with `INVALID_TARGET` before any activation or native launch, and a linked compliance
test holds that rule.

## DEBT [consistency]: an absent or unusable agent-token module ends recovery with a traceback

The local review of https://github.com/outcomeeng/plugins/pull/694, run
`2026-10-19_16-02-20-796-7460c0a782fd` on head 1e709fbcdcf3d6f793730e4f394d2b48e91e4bbe, raised this
as finding F-002 at `src/plugins/coding-agents/skills/recover-prowl-agents/scripts/recover_agents.py:137`.

**Evidence**: `_load_agent_tokens` and `_agent_token_class` raise `RuntimeError` at import time when
the sibling `agent_tokens.py` is absent, fails to execute, or declares no `AgentToken`. The message
opens with `error:`, but the exception escapes as a traceback. The same changeset makes
`/update-instruction-block` and `/review-changes` report the equivalent load failure of their
`agent-tokens.json` as one `error:` line with exit code 2, declares that behavior in
`spx/21-spec-tree.enabler/43-instruction-block.enabler/instruction-block.md`, tests it in both
nodes, and records it in the spec-tree changelog. No assertion of this node declares the
missing-module behavior, no test drives it, and the coding-agents changelog carries no entry for it.

**Impact**: a consumer whose installed coding-agents plugin lacks the module reads a traceback
instead of a one-line diagnostic. An intact installation always carries the module beside the script,
so the path runs only in a damaged install.

**Resolution shape**: catch the load failure where the module is imported, print the `error:` line on
stderr, and exit 2, as `review_result.py` does. Declare that behavior in this node's spec, link a
scenario test covering the absent, non-executing, and `AgentToken`-less module states, and add the
coding-agents changelog entry.

**Deferral reason**: the fix needs a decision line and a spec assertion that
outcomeeng/changes#120's record does not state. Its execution runs under a standing order that
forbids revising the record. The finding cites [`spx/15-spec-coverage.adr.md`](spx/15-spec-coverage.adr.md), which requires `[test]`
evidence for assertions about executable code. No assertion declares this path, and this node declares
`malleability: spec`, whose Passing requires no evidence beyond reachability and tagged results. A
follow-up Change states the decision line and the assertion, and carries the fix.

**Settlement condition**: an absent, non-executing, or `AgentToken`-less agent-token module makes
recovery print one `error:` line on stderr and exit 2. A linked scenario test holds that rule, and the
coding-agents changelog records it.

## DEBT [consistency]: recovery admits no candidate set without a current-session controller

`_validate_candidate_set` in `src/plugins/coding-agents/skills/recover-prowl-agents/scripts/recover_agents.py`
rejects a candidate set unless exactly one candidate carries `current-session` evidence. Prepare, activate,
recover, verify, and reassess each read the manifest through `_prepared_candidates`, so each rejects such
a set.

**Evidence**: running `prepare` for one Claude Code candidate (evidence `public-agent`) and one Codex
candidate (evidence `native-status`), each in its own Prowl pane, returned
`{"detail": "Recovery candidates require exactly one current-session controller.", "schemaVersion": 5, "status": "invalid-target"}`.
The session that ran the command holds no Prowl pane.

**Impact**: a session outside every Prowl pane cannot recover a set of Prowl panes. The writable-roots probe
ran only after the Author session moved into a Prowl pane and served as the controller; before that, its
protocol could not run without a candidate mislabeled as the controller.

**Resolution shape**: the node's spec and the exact-native-recovery decision state whether the controller is
required; the source and the compliance test follow the answer.

**Deferral reason**: the requirement is a stated product rule that no Change authorizes this changeset to
amend.

**Settlement condition**: the decision and the spec state the controller rule, and the source and linked
tests comply with it.

## DEBT [evidence]: the writable-roots probe runner has no deterministic test coverage

The probe runner `outcomeeng_testing/harnesses/writable_roots_probe.py`, about 1100 lines, runs through
the justfile recipe `probe-writable-roots-codex`. No test under `spx/**/tests` imports it, so no
assertion governs its pure helpers.

**Evidence**: the helpers `parse_status`, `root_listed`, `workspace_policy`, `server_attached`,
`expand_home`, `condense_screen`, `input_ready`, `command_pending`, `socket_paths`, and the admission
exclusion check, and the `CodexWritableRootProbe` flow with injected terminal, recovery, and runner
doubles, have no linked test. The local review run `2026-10-21_07-48-52-767-20eb803fc352` reported the
gap as an evidence finding on that file.

**Impact**: these helpers decide the INVALID stop conditions that the probe verdict relies on. A defect
in a helper can change a probe verdict or stop condition without any deterministic test failing.

**Resolution shape**: unit coverage of the runner is a separate, larger concern than the probe track.
It needs its own assertion design under this node, covering the helpers and the
`CodexWritableRootProbe` flow with injected doubles.

**Settlement condition**: co-located tests cover the helpers, with assertion design declared under the
owning node.

# Plan: Spec Auditing

The `audit-specs` skill and `spec-auditor` agent ship; the node is EXCLUDE'd until its eval suites land. Two follow-ups remain.

## Eval suites (un-EXCLUDE the node)

Author the `[eval]` suites the spec declares — `evals/structure/`, `evals/voice/`, `evals/tag-validity/`, `evals/prose-coupling/` (each `eval.toml` + `cases.jsonl` + `prompt.md`), mirroring `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/`. Replay a malformed/clean node spec through `/audit-specs` and grade the structured verdict (missing-section, malformed-kind-statement, heading-mismatch, temporal-voice, invalid-tag, evidence-type-mismatch, prose-coupling, APPROVED). Make the suites pass and remove the `spx/EXCLUDE` entry.

## Tree-wide prose-coupling cleanup

`audit-specs` (mis-tagged `[test]` assertion) and the `audit-tests` prose-coupling rule (prose-grep test) catch markdown-coupling violations laundered through test infrastructure. Once the skills are installed, dispatch `spec-auditor` and `test-evidence-auditor` across the tree and fix the known sites — retag the prose-bound `[test]` assertions to `[eval]`/`[audit]` and replace or remove the prose-grep tests in: `76-merging.enabler` (`test_merge_gate_policy.conformance`, `test_merge.conformance`), `76-merging.enabler/32-github-pr.enabler` (`test_github_pr.conformance`), `13-infrastructure.enabler/21-github-actions.enabler/54-runtime-operations.enabler` (`test_runtime_operations` scenario + property), and `68-reviewing.enabler/21-reviewing-changes.enabler` (`test_reviewing_changes`, laundered via the `reviewing_changes` harness). Audit each fix and ship per node.

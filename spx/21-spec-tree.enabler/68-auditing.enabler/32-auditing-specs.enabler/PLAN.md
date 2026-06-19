# Plan: Spec Auditing

The `audit-specs` skill and `spec-auditor` agent ship; the node is EXCLUDE'd until its eval suites land. Three follow-ups remain.

## Eval suites (un-EXCLUDE the node)

Author the `[eval]` suites the spec declares — `evals/structure/`, `evals/voice/`, `evals/tag-validity/`, `evals/prose-coupling/` (each `eval.toml` + `cases.jsonl` + `prompt.md`), mirroring `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/evals/`. Replay a malformed/clean node spec through `/audit-specs` and grade the structured verdict (missing-section, malformed-kind-statement, heading-mismatch, temporal-voice, invalid-tag, evidence-type-mismatch, prose-coupling, APPROVED). Make the suites pass and remove the `spx/EXCLUDE` entry.

## Register in the consumer dispatch reference

`AGENTS.md` carries the new `/audit-specs` → `spec-auditor` row. The consumer-facing copy does not: `src/plugins/spec-tree/skills/understand/templates/spx-claude.md` "Quick Reference: Skills and Agents" (and this product's rendered `spx/CLAUDE.md`) list `audit-adr`/`audit-tests` but not `audit-specs`. Add the row to the template, bump its `template_version`, and re-render via `/update-spx` so every consumer's guide picks it up. Deferred from the PR that added the skill because the template-version bump re-renders for all consumers — a larger blast radius than the skill addition itself.

## Tree-wide prose-coupling cleanup

`audit-specs` (mis-tagged `[test]` assertion) and the `audit-tests` prose-coupling rule (prose-grep test) catch markdown-coupling violations laundered through test infrastructure. Once the skills are installed, dispatch `spec-auditor` and `test-evidence-auditor` across the tree and fix the known sites — retag the prose-bound `[test]` assertions to `[eval]`/`[audit]` and replace or remove the prose-grep tests in: `76-merging.enabler` (`test_merge_gate_policy.conformance`, `test_merge.conformance`), `76-merging.enabler/32-github-pr.enabler` (`test_github_pr.conformance`), `13-infrastructure.enabler/21-github-actions.enabler/54-runtime-operations.enabler` (`test_runtime_operations` scenario + property), `68-reviewing.enabler/21-reviewing-changes.enabler` (`test_reviewing_changes`, laundered via the `reviewing_changes` harness), and `76-sessions.enabler/32-skill-surface.enabler` (`test_skill_surface`, laundered via the `skill_surface` harness). Audit each fix and ship per node.

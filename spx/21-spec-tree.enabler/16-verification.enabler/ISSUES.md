# Issues: Verification Enabler

## Downstream enforcement for `[audit]` decision-rule modes (deferred)

`spx/14-verification.pdr.md` carries four `[audit]` rules under `## Verification` / `### Audit` (an activity declares its type and purpose; a type's verdict mode is fixed by definition; a model never judges a deterministic type's verdict; the type set and the two verdict modes are closed). `spx/21-spec-tree.enabler/32-decisions.enabler/decisions.md` asserts that a decision record's rules flow into spec assertions that enforce them somewhere in the governed subtree — but an `[audit]`-mode rule is enforced by an auditing skill's judgment, not by a `[test]`/`[eval]` spec assertion, and no node spec yet enforces these four rules individually.

Establish how `[audit]` decision-rule modes are enforced downstream: either author node-spec `[audit]` assertions an auditing skill checks against each rule, or refine the `decisions.md` flow rule so it recognizes audit/eval enforcement for `[audit]`/`[eval]` modes. This is a methodology question broader than the verification-taxonomy change that introduced the modes.

Surfaced by the local `reviewing-changes` review on PR #103.

## Missing `[eval]` evidence on verification skill judgment surfaces

Every verification skill conforming to the contract in `verification.md` is an LLM-driven judgment producer. Per `spx/15-spec-coverage.adr.md`, judgment-surface assertions must carry `[eval]` evidence scored against curated cases through the `outcomeeng-evals` harness. PR #43 established the pattern for `reviewing-changes`; no other verification skill has followed it.

`/aligning` does not detect missing `[eval]` evidence — the check is by hand against `spx/15-spec-coverage.adr.md`.

**Pattern for each verification skill** (per-skill checklist):

1. **Eval directory layout.** One directory per judgment claim under `<verification-skill-enabler>/evals/<rule-slug>/`. Each carries:
   - `eval.toml` — `title`, `cases`, `prompt`, `threshold`, `trials` (per `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md` assertion #14).
   - `cases.jsonl` — one curated case per line. Each line is `{"id": ..., "input": {...}, "expected_verdict": {"must_contain": [...], "must_not_contain": [...]}}`.
   - `prompt.md` — self-contained instructions. Inline the rubric; do not require the model to invoke the real verification skill chain from inside the eval. The harness substitutes `{case_id}` and `{input_json}` placeholders.
   - `history.jsonl` — append-only run summaries, committed.
   - `runs/` — full transcripts, gitignored via `.gitignore`.
2. **Threshold.** `0.85` per marketplace precedent. Do not lower the threshold to pass a flaky case; fix the case or the review prompt.
3. **Wire shape.** Use the real verdict wire shape declared by the verification skill's policy module. The grader does structural subset matching.
4. **Coupling per case.** Every case carries verdict-level + finding-level expectations per eval-harness assertion #31.
5. **Concern separation.** One judgment surface per eval.

**Harness limitations to design around:**

- Tool-call trace is not captured; assertions about tool-use order fall back to self-report-based probes.
- List subset matching is multiset, position-independent — "X before Y" ordering cannot be expressed.
- Prompt token substitution is global — do not write `{case_id}` or `{input_json}` in comments.
- No alternation in expectations — relax via `must_not_contain` when OR semantics are needed.
- Cost: ~$0.28/case at sonnet rates.

**Affected skills:**

- `32-auditing-nodes.enabler` (candidate future skill) — when authored, must adopt this pattern.
- `spx/21-spec-tree.enabler/68-auditing.enabler/32-auditing-tests.enabler` — when implemented, eval evidence requirements are documented in its own PLAN.

## `reviewing` vs `auditing` vocabulary confusion in `verification-kinds.md` and `reviewing-changes` prompt

`src/plugins/spec-tree/skills/understanding/references/verification-kinds.md` correctly declares five verification types. The confusing boundary: `reviewing` is open-ended changeset judgment, while standards conformance is `auditing` and static/tool conformance is `validation`. The active `reviewing-changes` prompt currently implies standards comparisons the skill does not load enough context to perform.

**Fix:**

1. Reconcile `verification-kinds.md` so the `reviewing` entry emphasizes open-ended changeset review over quality, risk, consistency, evidence, and architecture, without implying standards-conformance audit.
2. Keep `spx/14-verification.pdr.md` on the five-type taxonomy; amend only if the grounding text needs the same boundary clarification.
3. Reconcile the reviewing node with the active `reviewing-changes` prompt and schema so any remaining review taxonomy buckets match what `reviewing-changes` can actually judge.
4. Gate the change with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, and `just docs-check`.

Handle before applying the Python, TypeScript, and Rust test-standard drift fixes recorded in `docs/cross-language-test-standards-drift-audit.md`.

## `verification.md` assertions still tagged `[audit]` where deterministic tests are feasible

Assertions 5 and 9 in `verification.md` (model-field presence) were retagged to `[test](tests/test_agent_model_field.mapping.l1.py)` in PR #160. Several other assertions remain `[audit]` where deterministic checks are feasible: agent-file location under `src/plugins/spec-tree/agents/`, `tools:` field declaration, and `skills:` field declaration.

**Fix:** Write compliance tests covering the remaining machine-checkable assertions and retag each from `[audit]` to `[test](...)` in both `verification.md` and `13-architecture.adr.md`. Address all machine-checkable assertions together to keep the spec internally consistent.

---

## Reference

- PR #43 — first eval pattern instance: `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/evals/`
- Eval-harness contract: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`
- Spec-coverage ADR: `spx/15-spec-coverage.adr.md`
- Verification PDR (taxonomy + lanes): `spx/14-verification.pdr.md`
- Verdict-format PDR (JSON, not XSD): `spx/15-audit-verdict-format.pdr.md`
- Precedent eval: `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/32-test-data-ownership.enabler/evals/shared-constant-bag/`

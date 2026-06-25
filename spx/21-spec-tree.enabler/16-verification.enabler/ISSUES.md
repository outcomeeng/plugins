# Issues: Verification Enabler

## Run-journal migration is in flight

`13-run-journal.adr.md` and `verification.md` declare present-tense product truth: every agentic verification run uses `spx journal` as its source of truth, and every surface is a projection from the sealed event prefix. Lower layers that still use the verdict toolchain or `thread_store` are therefore known migration debt, not fresh design choices.

Current disposition:

- `/audit` default local emit is on `spx journal` and the shared consumer projection; focused tests and live smoke tests passed. It still needs one real `/audit` workflow run before review migration starts.
- `review-changes` now persists through `spx journal --type review` and requires sealed terminal state matching the reviewed diff's `headSha`/`baseRef`/`baseSha`, `changedFiles`, `configDigest`, and status.
- Stateful audit-orchestrator cross-run folding is blocked until `@outcomeeng/spx` exposes an ordered read/list of a branch/type scope's sealed runs. Upstream session: `2026-06-23_07-42-10`.
- `spx journal render` is identity by design. Consumer-owned markdown/findings/check surfaces are projections over journal events; they are not channel render output.
- Keep the verdict schema and rollup helpers only while child audit skills still emit verdict JSON. Delete the remaining verdict toolchain and `thread_store` after their consumers migrate.

Use `PLAN.md` as the authoritative continuation map.

## Downstream enforcement for `[audit]` decision-rule modes (deferred)

`spx/14-verification.pdr.md` carries four `[audit]` rules under `## Verification` / `### Audit` (an activity declares its type and purpose; a type's verdict mode is fixed by definition; a model never judges a deterministic type's verdict; the type set and the two verdict modes are closed). `spx/21-spec-tree.enabler/32-decisions.enabler/decisions.md` asserts that a decision record's rules flow into spec assertions that enforce them somewhere in the governed subtree — but an `[audit]`-mode rule is enforced by an audit skill's judgment, not by a `[test]`/`[eval]` spec assertion, and no node spec yet enforces these four rules individually.

Establish how `[audit]` decision-rule modes are enforced downstream: either author node-spec `[audit]` assertions an audit skill checks against each rule, or refine the `decisions.md` flow rule so it recognizes audit/eval enforcement for `[audit]`/`[eval]` modes. This is a methodology question broader than the verification-taxonomy change that introduced the modes.

Surfaced by the local `review-changes` review on PR #103.

## Missing `[eval]` evidence on verification skill judgment surfaces

Every verification skill conforming to the contract in `verification.md` is an LLM-driven judgment producer. Per `spx/15-spec-coverage.adr.md`, judgment-surface assertions must carry `[eval]` evidence scored against curated cases through the `outcomeeng-evals` harness. PR #43 established the pattern for `review-changes`; no other verification skill has followed it.

`/align` does not detect missing `[eval]` evidence — the check is by hand against `spx/15-spec-coverage.adr.md`.

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

## `review` vs `audit` vocabulary confusion in `verification-kinds.md` and `review-changes` prompt

`src/plugins/spec-tree/skills/understand/references/verification-kinds.md` correctly declares five verification types. The confusing boundary: `review` is open-ended changeset judgment, while standards conformance is `audit` and static/tool conformance is `validate`. The active `review-changes` prompt currently implies standards comparisons the skill does not load enough context to perform.

**Fix:**

1. Reconcile `verification-kinds.md` so the `review` entry emphasizes open-ended changeset review over quality, risk, consistency, evidence, and architecture, without implying standards-conformance audit.
2. Keep `spx/14-verification.pdr.md` on the five-type taxonomy; amend only if the grounding text needs the same boundary clarification.
3. Reconcile the review node with the active `review-changes` prompt and schema so any remaining review taxonomy buckets match what `review-changes` can actually judge.
4. Gate the change with `spx validation markdown`, `spx spec status --format json`, `just check-skills`, and `just docs-check`.

Handle before applying the Python, TypeScript, and Rust test-standard drift fixes recorded in `docs/cross-language-test-standards-drift-audit.md`.

## `verification.md` assertions still tagged `[audit]` where deterministic tests are feasible

Assertions 5 and 9 in `verification.md` (model-field presence) were retagged to `[test](tests/test_agent_model_field.mapping.l1.py)` in PR #160. Several other assertions remain `[audit]` where deterministic checks are feasible: agent-file location under `src/plugins/spec-tree/agents/`, `tools:` field declaration, and `skills:` field declaration.

**Fix:** Write compliance tests covering the remaining machine-checkable assertions and retag each from `[audit]` to `[test](...)` in both `verification.md` and `13-run-journal.adr.md`. The machine-checkable set is the wrapper-agent structural rules named above (agent-file location, `tools:` field, `skills:` field); the run-journal contract assertions (append, cursor, seal, projection, backend-neutral channel) are NOT in this set — they become deterministically testable only once the `spx` CLI run-journal verbs land (this node's `PLAN.md`), and stay `[audit]` until then. Address all machine-checkable assertions together to keep the spec internally consistent.

---

## Reference

- PR #43 — first eval pattern instance: `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/evals/`
- Eval-harness contract: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`
- Spec-coverage ADR: `spx/15-spec-coverage.adr.md`
- Verification PDR (taxonomy + lanes): `spx/14-verification.pdr.md`
- Result-delivery PDR (incremental reveal, same shape on local and PR surfaces): `spx/15-audit-result-delivery.pdr.md`
- Verdict JSON schema (the prior XSD-based node has been removed): `spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler/verdict-toolchain.md`
- Precedent eval: `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/32-test-data-ownership.enabler/evals/shared-constant-bag/`

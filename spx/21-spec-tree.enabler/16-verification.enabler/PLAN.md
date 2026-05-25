# PLAN — Shared verification eval design pattern

## Why

Every verification skill that conforms to the contract in `verification.md` is an LLM-driven judgment producer. Per `spx/15-spec-coverage.adr.md`, the verification skill's judgment-surface assertions must carry `[eval]` evidence scored against curated cases through the `outcomeeng-evals` harness. PR #43 established the pattern for the first verification skill (`reviewing-changes`). This plan captures the design decisions future verification skills should mirror, plus the harness limitations discovered along the way.

`/aligning` does not detect missing `[eval]` evidence — the check is by hand against `spx/15-spec-coverage.adr.md`.

## The pattern (per-skill checklist)

For every verification skill that conforms to the contract:

1. **Eval directory layout.** One directory per judgment claim under `<verification-skill-enabler>/evals/<rule-slug>/`. Each carries:
   - `eval.toml` — `title`, `cases`, `prompt`, `threshold`, `trials` (per `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md` assertion #14).
   - `cases.jsonl` — one curated case per line. Each line is `{"id": ..., "input": {...}, "expected_verdict": {"must_contain": [...], "must_not_contain": [...]}}`.
   - `prompt.md` — self-contained instructions. Inline the rubric; do not require the model to invoke the real verification skill chain from inside the eval. The harness substitutes `{case_id}` and `{input_json}` placeholders.
   - `history.jsonl` — append-only run summaries, committed. Developer-machine appends become git-diff noise that contributors restore; CI owns canonical baseline appends.
   - `runs/` — full transcripts, gitignored via `.gitignore`.

2. **Threshold.** `0.85` per marketplace precedent (`spx/.../shared-constant-bag/eval.toml`). Do not lower the threshold to pass a flaky case; fix the case or the review prompt. Per `spx/15-spec-coverage.adr.md` and the marketplace's never-weaken-the-spec rule, the spec governs, not the model.

3. **Wire shape.** Use the real verdict wire shape declared by the verification skill's policy module — the same JSON the verification skill emits to its arbiter. Do not invent a simplified probe shape unless the verification skill has no policy module. The grader does structural subset matching, so cases need only specify the fields under test; the model still emits the full schema.

4. **Coupling per case.** Every case carries verdict-level + finding-level expectations per eval-harness assertion #31. Two acceptable shapes:
   - Strict (#36-compliant): both signals in one `must_contain` entry, e.g. `[{"decision": "request_changes", "findings": [{"severity": "must_fix", "concern": "security"}]}]`.
   - Pragmatic split: verdict-level in `must_contain`, finding-level in `must_not_contain`. Acceptable when the case's natural shape requires the model to emit zero findings (clean diffs); the forbidden-pattern check still couples the case structurally.

5. **Concern separation.** One judgment surface per eval. Mixing protocol probes (does the agent invoke the arbiter?) with judgment-direction probes (does decision match diff quality?) makes failures hard to attribute. PR #43's wrapper-protocol eval initially conflated these — narrowing it to tool-call presence only was the fix.

## Harness limitations — design around them

These cannot be worked around inside the harness. Eval design must accommodate them.

- **Tool-call trace is not captured.** The harness records the final assistant message only. Assertions about agent runtime tool-use order (`validate_review_result.py` before `write_record.py`) fall back to self-report-based probes — the model lists its planned tool calls in the final response. Self-report is weaker than observed behavior; flag the limitation in the prompt so it is visible.
- **List subset matching is multiset, position-independent.** The grader's `is_subset` checks presence and cardinality, never order. Assertions of the form "X before Y" cannot be expressed as a subset match against a `tool_calls` array; the eval can only check that both X and Y are present.
- **Prompt token substitution is global.** Do NOT write `{case_id}` or `{input_json}` in comments or descriptive sections of `prompt.md` — the harness substitutes every occurrence in the file. Rephrase to "the case id is substituted by the harness" / "the input JSON tokens follow" without the literal placeholders.
- **No alternation in expectations.** The grader has no OR semantics. A case that must accept either `decision == "approve"` or `decision == "comment"` cannot express that in `must_contain`; the alternative is to relax via `must_not_contain` (forbid the wrong direction) and drop the strict requirement on the right direction.
- **Cost.** ~$0.28/case at sonnet rates. A 4-eval × 6-case suite costs ~$7. Re-running for calibration adds proportionally.

## When to adopt the pattern

- A new verification skill conforms to the contract → MUST carry `[eval]` evidence on its judgment surface before the spec is considered complete.
- An existing verification skill has `[review]` tags on runtime LLM-behavior assertions → those are placement violations against `spx/15-spec-coverage.adr.md`. Re-tag to `[eval]` with an eval that probes the behavior (PR #43 did this for `reviewing-changes` against `evals/wrapper-protocol/`).
- An existing verification skill has zero `[eval]` assertions on its judgment surface → its core deliverable is uncovered. Build evals per the pattern.

## Future verification skills anticipated

- `32-auditing-nodes.enabler` (a candidate future verification skill) — when authored, will adopt the shared verification contract and this eval pattern.
- `spx/21-spec-tree.enabler/68-auditing.enabler/32-auditing-tests.enabler` (has its own PLAN.md) — when implemented, the test-auditing skill is a candidate verification skill; its eval evidence requirements are documented in its own PLAN.

## Reference

- PR #43 — first instance of this pattern: `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/evals/`
- Eval-harness contract: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md`
- Spec-coverage ADR: `spx/15-spec-coverage.adr.md`
- Evidence-execution-lanes ADR: `spx/16-evidence-execution-lanes.adr.md`
- Verdict-format PDR (JSON, not XSD): `spx/15-audit-verdict-format.pdr.md`
- Precedent eval (the only existing one before PR #43): `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/32-test-data-ownership.enabler/evals/shared-constant-bag/`

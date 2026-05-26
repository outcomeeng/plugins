# PLAN — cascade the validity+phase gate model

Deferred to a fresh session. `spx/15-agent-pr-authority.pdr.md` was rewritten to the corrected model; this node's spec, its evals, and the skills it governs still encode the old severity-gated, promotion-gated model. The `pdr-auditor` REJECTED `spx/15-agent-pr-authority.pdr.md` on downstream-flow for exactly this gap — the corrected rules govern nothing until the surfaces below align.

## The corrected model (source: spx/15-agent-pr-authority.pdr.md)

- The PR authority gate governs autonomous **merge** only, from observable state: closure gate passed, required checks terminal-green on the pushed head, a current-head review exists with every finding resolved (applied in-PR or recorded as a deferred item), five-minute settle, branch hygiene including upstream-safety, no production-class markers.
- Draft → ready promotion is **not a gated action**: the agent flips ready mechanically before merge. No promotion gate, no promotion-authority overlay topic, no "promotion fires CI" framing.
- The agent acts on each finding by **validity** (backed by the cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions; drop the unbacked) and **phase** (before push: apply every valid finding, splitting the changeset when a fix is too large; PR open: apply every valid finding that does not substantively widen the PR, record the rest per the project's deferral guidance) — **never by severity**. Severity is a reporting label.

## Surfaces to cascade

### Spec — `merging.md`

- Scenario ~line 11: replace the severity predicate ("a current-head three-severity review … has no unresolved `BLOCKING` or `DEBT`") with "a current-head review exists with every finding resolved (applied in-PR or recorded as a deferred item)"; replace "authorizes both draft → ready promotion and merge from one verdict" with merge only.
- Promotion scenarios ~lines 12–14: production scenario → withholds merge (drop "for promotion and for merge"); remove the overlay-human-promotion scenario (promotion is not gated); overlay-human-merge scenario → keep, drop "performs autonomous promotion".
- local-review-gate scenario ~line 16: replace the severity STOP/PROCEED rule with the before-push validity+phase rule — the operator validates each finding and applies every valid one before push, splitting the changeset when a fix is too large; an unbacked finding is dropped.
- Compliance ~lines 21, 23: drop the "promotion versus merge" framing; state one merge verdict.
- PROVIDES / CAN (lines 3–5): reframe "one observable authority model" so it does not imply a promotion gate.

### Evals — `evals/`

- `local-review-gate`: redesign. The gate decision is no longer STOP/PROCEED on severity; probe validity (an unbacked finding is dropped) and phase (every valid finding applied before push).
- `merge-command-overlay-precedence/prompt.md`: drop the severity criterion ("current-head three-severity review with no blocking or debt").
- `authority-gate-green` / `authority-gate-production` / `authority-gate-hygiene`: merge-only; the review predicate is "every finding resolved", not severity.
- `overlay-human-promotion`: remove (promotion is not gated). `overlay-human-merge`: keep.
- Re-running the redesigned evals costs API budget — gate that behind a deliberate run.

### `ISSUES.md`

- The reviewer-skipped item (~line 9) uses the old "three-severity review" framing and treats the prior PDR MUSTs as baseline — realign to "a current-head review with findings resolved" and the corrected reviewer-skipped exception.

### Skills — `src/plugins/spec-tree/skills/` (rebuild `dist/` after)

- `standardizing-merging/SKILL.md`:
  - `<pr_authority_gate>`: rewrite per the PDR — merge predicate is findings-resolved, not severity; drop the promotion transition and the "promotion fires expensive CI / after CI converges" framing; draft/ready is a mechanical flag.
  - `<review_classification>`: severity stays the reporting label, but the operator's handling is validity+phase, never severity-routing.
  - `<action_tokens>`: drop promotion tokens (e.g. `MARK_READY`); keep merge and mention tokens.
  - `<repo_local_overlay>`: drop the draft-promotion-authority topic; keep merge authority.
- `opening-pr/SKILL.md` Step 3: validity+phase — validate each finding (drop the unbacked), apply every valid finding before push, split the changeset when a fix is too large; no severity STOP.
- `managing-pr/SKILL.md`: Step 5 (drive queue) → validate, apply every non-substantively-widening valid finding, record the rest per deferral guidance; Step 8 → merge gate keys on findings-resolved, draft/ready flipped mechanically, promotion not gated.

### Docs

- `AGENTS.md` and `spx/AGENTS.md` local-review-gate bullet, and `src/plugins/spec-tree/skills/bootstrapping/templates/spx-claude.md` gate bullet: severity-stop → validity+phase.

## After the cascade

- `just build-skills` (rebuild `dist/claude` + `dist/codex`), then `just check` green.
- Re-run `pdr-auditor` on `spx/15-agent-pr-authority.pdr.md`; downstream-flow must PASS.
- Run `changes-reviewer` to zero findings.

## Cross-references

- Reviewer-side framing fix: `spx/21-spec-tree.enabler/68-reviewing.enabler/PLAN.md`.
- The `@spec-tree` mention-trigger default is already corrected in the skills; do not reintroduce `@claude`.

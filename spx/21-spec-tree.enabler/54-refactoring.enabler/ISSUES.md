# Issues: Refactoring Enabler

## Post-mutation validation has no command-backed gate

The skill moves, removes, and consolidates Spec Tree nodes, then closes through a checklist without
running deterministic validation. A future `/refactor` change must add explicit pass/fail gates using
the product's author and verify commands, including `spx validation markdown` and
`spx spec status --format json`, before reporting a refactored tree as successful.

**Trigger to revisit:** the `/refactor` implementation workflow is next changed. **Resolution shape:**
run the deterministic commands after mutation, stop on either nonzero result, and make their passing
results part of the skill's success contract.

## FOLLOW-UP [architecture]: no skill guides a methodology-wide refactor (terms, structure, authority) across this repo's self-describing surfaces

`/refactor` covers moving and re-scoping **spec-tree nodes** — tree surgery. It does not cover refactoring the **spec-tree methodology itself**: a rename of a methodology concept, a restructure of an assertion layout, or a relocation of selection authority, propagated across every surface that *describes* the methodology. The two recent vocabulary PRs (#144 verification-type/assertion-type rename; #145 per-plugin bump fix) each took ~5 local + CI review rounds to converge. That round count is the symptom; the missing skill is the cause.

### What went wrong (analysis from PR #144 / #145)

1. **Blast radius discovered incrementally, not mapped upfront.** A single methodology term (`evidence type` → `assertion type`, `evidence lane` → `verification type`) appears as: prose, Markdown table headers, XML section anchors (`<evidence_mechanisms>` → `<verification_types>`), spec assertion text, decision-template placeholders (`[{evidence type}]`), filename tokens (`<evidence>`), audit rule codes (`evidence-type-mismatch`), and self-referential examples. It lives in the foundation references, the decision templates, the node templates, the governing specs, **every skill body across every plugin including the language plugins**, the `instruction-block` template **and** its rendered `spx/CLAUDE.md`/`AGENTS.md`, `README.md`, and the regenerated `dist/` trees. Each review round surfaced one more missed surface (the `/test` skill — the very authority selection was being relocated *to* — still said "evidence type"; the language plugins said "evidence mode"; `AGENTS.md`/`README.md` described the old behavior). A single deterministic enumeration of the full surface before the first commit would have collapsed the rounds.

2. **Mechanical substitution introduced semantic errors.** Replacing `lane` → `verification type` without re-reading each sentence produced a false statement in `spx/CLAUDE.md`/`AGENTS.md` and the template: "the verification type is declared per project" — the verification type comes from the tag, not per-project config; the original meant the *eval runner* is per-project. A methodology rename needs a per-occurrence **semantic** pass, not find-replace.

3. **Same word, different concept, conflated.** `evidence` is a legitimate noun (the proof a test gives; "evidentiary value"; the audit "evidence model"); the `/decompose` ordering matrix has an "Evidence type" column meaning the *ordering-reason kind*; the filename segment `<evidence>` holds the assertion type. A blanket rename would have corrupted all three. Distinguishing concept-name occurrences (rename) from homonyms (leave) from tokens/rule-codes (defer or coordinate) required judgment the agent applied only reactively, per review finding.

4. **Self-authored prose churn.** Several rounds were spent on grammar run-ons and self-contradictions the agent introduced into its own `AGENTS.md`/`README.md`/`bump.md` edits (a run-on "adds a second plugin bumps that plugin"; calling DRY_RUN a "write pass" two lines above an assertion declaring it read-only). Prose edits to instruction surfaces were made without re-reading the full sentence in context.

5. **Entangled tokens deferred without a map.** The `<evidence>` filename-segment rename touches a product PDR, every `spx/**/tests/` filename, and the validators; the `evidence-type-mismatch` audit rule code is tied to unbuilt adr/pdr-auditing eval suites. These were correctly deferred — but only after a review round flagged them, not because a refactor checklist surfaced "this token has eval/validator entanglement; scope it out up front."

### Root cause

Refactoring the methodology is categorically harder than refactoring a node because the methodology **describes itself** in many interlocking places, in many syntactic forms, across the repo's two audiences (authored `src/plugins/` → portable consumer output; this repo's own `spx/` + meta-instructions in `AGENTS.md`/`README.md`). `/refactor` has no model for this.

### Suggestion: a repository-specific methodology-refactoring skill

Create a skill scoped to **this repository** (it is meta-tooling for the methodology's own dev repo, not shipped to consumers — so a `spx/local/` overlay or a non-shipped skill, not the consumer-facing `/refactor`). It would, before the first commit:

- **Enumerate the complete surface deterministically** from a checklist: foundation references + their XML anchors; decision templates; node templates; governing specs; every skill body across every plugin (incl. language plugins) and agents; the `instruction-block` template **and** the rendered `spx/CLAUDE.md`/`AGENTS.md`; `README.md`; `dist/` regen. Plus the inverse for tokens: filename segments, audit rule codes, eval/validator references.
- **Classify each occurrence** as concept-name (rename), homonym (leave — e.g. `evidence` the proof-noun, the `/decompose` "Evidence type" ordering column), or entangled token (defer/coordinate — filename segment, rule code with eval suites), and record the disposition.
- **Require a semantic re-read of every renamed occurrence** — explicitly flag mechanical substitutions that change meaning (the "verification type is declared per project" failure).
- **Run one comprehensive grep-sweep + one per-surface semantic pass before the first commit**, so local and CI review converge in one round.
- **Honor the two-audience split** and the spec→test→code truth hierarchy (rename the spec assertion first; conform implementation and tests to it).

Target: a methodology refactor lands review-clean in one round instead of five.

Surfaced while shipping the verification-type/assertion-type vocabulary reconciliation (PR #144) and the per-plugin bump fix (PR #145), 2026-06-09.

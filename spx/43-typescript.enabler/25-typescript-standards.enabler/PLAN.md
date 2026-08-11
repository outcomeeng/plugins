# Plan: align TypeScript standards subtree to the evidence-routing foundation

Coordination note for the TypeScript-only slice. Reconcile against current specs,
decisions, and the plugins-e foundation before acting — a note is a stale-prone input,
not authority.

## Progress

The evidence foundation advanced beyond the plan below. plugins-e's PR #468
(`ce11687f8`) shipped the shared `test-evidence-standards` (prose-only, named XML
sections), rebuilt `audit-typescript-tests` (composes `/audit-tests`, specializes the
9-category coupling supplement inline, attributes predicate-ownership), and fixed the
`<dependency_injection>` exemplar. #468 also rewrote the cited governance
(`test-verification.md`, `15-test-infrastructure.pdr.md`) to the semantic-binding-ownership
model. `audit-typescript-architecture` was already pure enforcement.

Remaining TypeScript work, in order:

1. **Spec alignment (this slice) — DONE on branch `work/ts-spec-foundation-alignment`.**
   The 8 spec files aligned to the semantic-binding foundation: the old absolute "NEVER
   declare variables or constants" replaced by semantic-binding ownership citing
   `test-verification.md`; 65 `[review]` → `[audit]`; "evidence type" → "assertion type";
   parent/child facet split (parent owns the predicate seam, `32-test-data-ownership` owns
   binding-by-data-choice), and the paired predicate-seam audit assertion in
   `43-test-infrastructure-auditing`. Gated APPROVED by per-node `spec-auditor` runs.
2. **Property predicate-seam reconciliation.** `typescript-test-standards`
   `<property_based_testing>` and `audit-typescript-tests:132` still say the invariant lives
   in the imported property harness, contradicting the shared `<assertion_type_litmus>`
   ("the invariant remains in the linked test"). Reopens plugins-e's just-merged skills.

   **Dependency cleared, and the shape is now decided.** `test-evidence-standards` is on
   `origin/main`. Its `<predicate_seam>` requires every assertion API call to be lexically
   visible in the linked test; `<assertion_type_litmus>` requires the property invariant to
   remain in the linked test while the generator owns the domain. The harness keeps seed,
   run count, and replay diagnostics and nothing else — the split
   `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`
   ALWAYS:25 already implies. The Rust plugin was corrected to that shape first; see
   `spx/43-rust.enabler/PLAN.md`, whose worked examples are the reference for this slice.

   **Site inventory, measured against the shipped skill.** Nineteen example sites across
   `typescript-test-standards`, in three classes:

   - **Twelve bare delegations** — `await assertX(...)` as the whole test body, no `expect`.
     `references/exception-implementations.md:15,19,36,42,62,68,85,102`;
     `references/l1-patterns.md:53`; `references/l2-patterns.md:13,17`;
     `levels/l1-local-deterministic.md:73`; `levels/l2-local-infrastructure.md:35`.
   - **Six property-run delegations** — `assertProperty(...)` moving the whole run into the
     harness. `SKILL.md:204-207` (the four-row pattern table);
     `references/l1-patterns.md:20`; `levels/l1-local-deterministic.md:54`.
   - **One naming-only defect** — `levels/l3-remote-credentialed.md:34` keeps `expect` in the
     test and reads `await expect(assertSignedStripeFixtureAccepted()).resolves.toMatchObject(...)`.
     The seam holds; the helper name asserts something it does not do. Rename, do not restructure.

   Class 1 and class 2 contradict this subtree's own
   `43-test-infrastructure-auditing.enabler/test-infrastructure-auditing.md:16`, which already
   forbids an imported harness that "itself calls `expect`, an assertion API, or a matcher".
   The spec is right and the shipped examples are wrong, so this is skill-content work only —
   no spec assertion changes.

   Scope was held to Rust by operator decision when both defects were on the table together.
3. **`audit-typescript-code`** — heaviest of the three auditors; minor alignment to the
   pure-enforcement shape at most.

The Goal/Foundation sections below predate #468 and are retained as the derivation trail;
treat the Progress list above as current.

## Goal

Three coupled corrections, driven by the PR 459 evidence-routing foundation (see
"Foundation reshaping" below):

1. **Make author and auditor consume ONE standard.** `/test-typescript` (author) and
   `/audit-typescript-tests` (auditor) must both consume the same independently loadable
   test-evidence standard for every rule they both enforce. The auditor stops restating
   rule lists, coupling taxonomies, and evidence-property tables; it refers to the shared
   standard and judges by the criterion the standard states. Same shape for
   `audit-typescript-code`/`architecture` against their standards.
2. **Reduce the TypeScript specs and skills to language EXPRESSION.** Generic
   concerns — assertion typing, execution-level selection, source-contract and oracle
   gates, evidence-property checks, exception classification, naming — belong to the
   generic `/test` and the shared standard, not to TypeScript. The TypeScript subtree
   keeps only TypeScript-specific expression (`@testing/` path mapping, `fast-check`,
   `vitest`/`playwright`, tsconfig mechanics) and delegates the rest.
3. **Fix the assertion-delegation exemplars in `typescript-test-standards`.** The skill
   teaches that executed test files should delegate assertion flow into harnesses, which
   contradicts `test-verification.md:12` ("executed test files contain assertion flow
   only"). Correct the exemplars so the executed test file owns the assertion flow.

## Foundation reshaping — PR 459 evidence-routing (merged, `4c89e84e9` + `/verify`)

Read `spx/21-spec-tree.enabler/35-evidence.enabler/{evidence.md, 39-test-skill.enabler/test-skill.md, 69-verify-skill.enabler/verify-skill.md, PLAN.md, ISSUES.md}`.
This is the change plugins-e missed; it moves the basis of the whole TypeScript subtree.

- **One independently loadable standard, consumed by both author and auditor.**
  `evidence.md:14` — "an evidence-authoring workflow and its evidence auditor consume the
  same independently loadable standards source for every rule they both enforce."
  `test-skill.md:12` — "test authoring and test auditing consume one independently loadable
  standard for coupling, falsifiability, alignment, coverage, source ownership, domain
  variation, oracle independence, and controlled implementations." The author/judge
  symmetry below is now foundation law, not inference. That single standard is plugins-e's
  `test-evidence-standards` (NOT yet on `origin/main`).
- **Generic vs language-EXPRESSION split.** `test-skill.md:11` — the generic `/test` owns
  assertion typing, execution-level selection, source-contract/oracle gates,
  evidence-property checks, exception classification, naming. `35-evidence/PLAN.md:37-39` —
  those move out of language workers; "language skills carry only language-specific
  expression and commands."
- **Verification-type routing through `/verify`.** `verify-skill.md:24` — every workflow
  that delegates verification-type selection invokes `/verify`, then test→`/test`,
  eval→`/eval`, audit→pathless isolated verifier. `/test` is now the generic specialist.
- **Vocabulary retired.** `35-evidence/ISSUES.md:11` retires "evidence type", "evidence
  lane", "evidence mechanism", "evidence mode", and "claim" as a structural term. Canonical:
  **verification type** (test/evaluate/audit) and **assertion type** (scenario/mapping/
  conformance/property/compliance, testing only).
- **Tag set closed.** `verify-skill.md:22` — "NEVER: recognize, name, alias, or translate
  any tag outside the verification-type set" {test, eval, audit}. `[review]` is outside the
  set: the migration below is foundation-mandated, not hygiene.

## Node set (ascending index order — /apply work queue)

Counts are `[review]` assertions on `origin/main` at `9fef3cd1b`. Total: 65 `[review]`,
1 `[eval]`, 0 `[audit]`. The **RECLASSIFY** tag marks nodes that currently restate generic
concerns and must be reduced to TypeScript expression per the split above.

```text
spx/43-typescript.enabler/25-typescript-standards.enabler                        (3 review)
  21-typescript-architecture.enabler                                             (6 review)
  25-typescript-tests.enabler                                                   (12 review)
    21-source-testability.enabler                              (6 review)   RECLASSIFY
    32-test-data-ownership.enabler                       (12 review, 1 eval)  RECLASSIFY (partial)
    43-test-infrastructure-auditing.enabler                   (11 review)   RECLASSIFY
    54-execution-level-guidance.enabler                        (8 review)   RECLASSIFY
  29-typescript-code.enabler                                                     (7 review)
```

RECLASSIFY basis: `source-testability`, `execution-level-guidance`, and
`test-infrastructure-auditing` restate generic testability, level-selection, and
evidence-chain-audit rules that `test-skill.md:11-12` assigns to the generic specialist and
shared standard. `test-data-ownership` mixes generic ownership rules (generic) with the
`@testing/`-mapped homes and `fast-check` specifics (TypeScript expression, retained).
The precise per-assertion generic-vs-expression split is done at execution time against the
merged shared standard.

## Governing decisions (loaded, `origin/main` at `9fef3cd1b`)

- `spx/21-spec-tree.enabler/35-evidence.enabler/evidence.md` — single-loadable-standard
  mandate (`:14`), one-verification-type-selection-first (`:13`), acyclic routing (`:15`).
- `spx/21-spec-tree.enabler/35-evidence.enabler/39-test-skill.enabler/test-skill.md` —
  generic test specialist owns generic decisions (`:11`); one standard for author+auditor
  (`:12`); language specialist never repeats a generic decision (`:13`).
- `spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/verify-skill.md` —
  `/verify` routing; closed tag set (`:22`).
- `spx/21-spec-tree.enabler/17-audit.adr.md` — auditor composition: the language auditor
  holds only language-specific concerns; generic decision-record judgment is the
  artifact-type auditor's; language examples belong in `audit-{lang}-*`.
- `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`
  — `:12` "executed test files contain assertion flow only"; `:16` bans a binding that
  *changes ownership* (laundering), not all bindings. The exemplar defects contradict `:12`.
- `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`
  — harnesses manage resources and property-run config; do not own truth or replace behavior.
- `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` — five-type
  taxonomy; `[audit]` verdicts run in an isolated verifier context.

## The two exemplar defects in typescript-test-standards (src/plugins/typescript/skills/typescript-test-standards/SKILL.md)

Verify line numbers against the current file before editing — pre-compaction reading was
`<dependency_injection>` ~168-176 and `<property_based_testing>` ~183-188; the file was not
in the PR 459 base delta but re-confirm.

- `<dependency_injection>` exemplar: executed test body is a single harness call
  (`await assertPaymentGatewayRecordsCharge(PaymentProcessor);`) with **zero `expect`** —
  the harness owns the assertion. Contradicts `test-verification.md:12` and
  `15-test-infrastructure.pdr.md`. Fix: test file owns the assertion flow; harness provides
  the resource/double only.
- `<property_based_testing>` exemplars: `assertProperty(parserRoundtripProperty())`
  pre-builds the predicate outside the test file. The predicate is assertion flow and
  belongs in the test; the generator/harness supplies domain and run config.
- Line ~203 ("Executed TypeScript test files do not declare `const`/`let`/`var`…") is
  absolute and reads as banning assertion-flow locals — reconcile with `test-verification.md:16`
  (bans ownership laundering, not all bindings). NOTE the SAME over-broad rule is asserted at
  the SPEC layer: `typescript-tests.md:19`, `test-data-ownership.md:21`,
  `test-infrastructure-auditing.md:21` all say "NEVER declare variables or constants". These
  spec assertions must be reconciled to the foundation in the same slice — this is the
  "TypeScript skills AND spec alignment" scope.

## Author/judge symmetry (now foundation law)

Pre-compaction measurement: `audit-typescript-tests` loads `spec-tree:audit-tests`;
`test-typescript` does not — so a TypeScript-test author cannot see the criteria it will be
judged by. `evidence.md:14`/`test-skill.md:12` now mandate the fix: both consume the one
shared standard. Re-measure `test-typescript`'s loaded skill set after the `/test`→`/verify`
relegation (`test/SKILL.md`, `test/references/methodology.md` changed in PR 459) before
treating the old numbers as current.

## Coupling-taxonomy drift

`audit-typescript-tests` restates a 6-row coupling table against 9 rows in `/audit-tests`,
dropping **Laundered indirect**, **None**, **Prose-coupling**. Under the single-standard
model the table is not restated at all — the auditor refers to the shared standard's list.

## Auditor-as-loop target shape (~70-90 lines, from ~448)

```text
<objective> <constraints> <prerequisites> <audit_scope>
<audit_loop>
  For each rule in the referenced (shared + language-expression) standard:
    1. applicable to this subject? -> no: NOT_APPLICABLE + why
    2. judge by the rule's own stated criterion
    3. emit PASS | FAIL with rule address, artifact, evidence
  Then delegate generic evidence properties to the generic test-evidence audit; merge by name.
<verdict_format> <success_criteria>
```

The auditor MUST NOT enumerate a list of its own (a second inventory drifts). Rule
addressing uses the spec-tree-native positional form (containing skill + section +
sibling-local index), not a flat global id registry — a tombstone/global-id scheme was
retracted as contrary to `<ordering_model>` and `<declarations>`.

## Touched-file debt (fix-now on every node this slice edits)

- **`[review]` → `[audit]`** on every edited node (65 occurrences). Foundation-mandated by
  `verify-skill.md:22` (closed tag set), not just legacy spelling. Text unchanged, tag only;
  gate each with the spec auditor.
- **"evidence type" → "assertion type"** in the touched spec files (`typescript-tests.md:3,11`)
  — retired term per `35-evidence/ISSUES.md:11`. One skill-body residue remains outside this
  spec-only slice — `audit-typescript-tests/SKILL.md:55` ("misdeclares its evidence type") —
  retired in the property predicate-seam slice above, which already edits that skill under
  the skill-auditor gate.
- From this node's ISSUES.md: "Top-Level Specs Restate Methodology" (the three top-level
  child specs use generic methodology-layer assertions) and "[eval] Coverage Beyond the
  Slice" (candidates for `[review]`→`[eval]` migration once the auditor emits structural
  verdicts the grader can match).

## Dependency — do not start before this clears

The slice delegates the TypeScript standards *to* the single shared test-evidence standard
(plugins-e's `test-evidence-standards`, confirmed NOT on `origin/main`). Merge order:
plugins-n (PR 459, MERGED) → plugins-e → plugins-c. Start only on plugins-e's merge, which
carries:

- final section list of `src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md` and
  whether it ships explicit rule addresses (so the auditor loop can cite them) or prose-only;
- settled state of `test/SKILL.md`, `test/references/methodology.md`, and
  `test-typescript/SKILL.md` after the `/test`→`/verify` relegation.

## Revisit condition

Replace this plan with the executed slice once `test-evidence-standards` is on
`origin/main`. Re-run `/contextualize` on this node after that merge — the delegation
target and the `/test` skill will have changed again.

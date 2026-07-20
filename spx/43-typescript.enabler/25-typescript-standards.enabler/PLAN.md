# Plan: strip TypeScript auditors to pure standards enforcement

Coordination note for the TypeScript-only slice. Reconcile against current specs,
decisions, and the plugins-e foundation before acting — a note is a stale-prone input,
not authority.

## Goal

Two coupled corrections to the shipped TypeScript plugin skills:

1. **Strip the auditors to pure enforcement.** `audit-typescript-code`,
   `audit-typescript-tests`, and `audit-typescript-architecture` must contain only what
   *enforces* `typescript-standards`, `typescript-test-standards`, and
   `typescript-architecture-standards`. Everything an auditor restates — its own rule
   lists, coupling taxonomies, evidence-property tables — is deleted; the auditor refers
   to the standard that owns the list and judges by the criterion the standard states.
2. **Fix the assertion-delegation exemplars in `typescript-test-standards`.** The skill
   teaches that executed test files should delegate assertion flow into harnesses, which
   contradicts the governing decision (below). Correct the exemplars so the executed test
   file owns the assertion flow.

## Node set (ascending index order — /apply work queue)

Counts are `[review]` assertions in each node spec on the merged base (`origin/main` at
`6414f1b4`). Total: 65 `[review]`, 1 `[eval]`, 0 `[audit]`.

```text
spx/43-typescript.enabler/25-typescript-standards.enabler                                   (3 review)
  21-typescript-architecture.enabler                                                        (6 review)
  25-typescript-tests.enabler                                                              (12 review)
    21-source-testability.enabler                                                           (6 review)
    32-test-data-ownership.enabler                                                    (12 review, 1 eval)
    43-test-infrastructure-auditing.enabler                                                (11 review)
    54-execution-level-guidance.enabler                                                     (8 review)
  29-typescript-code.enabler                                                                (7 review)
```

## Governing decisions (loaded, merged base)

- `spx/21-spec-tree.enabler/17-audit.adr.md` — the auditor composition model. The language
  auditor holds **only** language-specific concerns; generic decision-record judgment
  (section structure, atemporal voice, tag validity) is the artifact-type auditor's, and
  language-specific examples/commands/patterns belong in the `audit-{lang}-*` skill, not in
  orchestration. This ADR is the spine of correction (1): the strip-to-enforcement work
  *enforces* it.
- `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md`
  — line 12: "executed test files contain assertion flow only; values, expected outputs,
  reusable cases, property-test settings, setup policy, and lifecycle policy live in source
  contracts, spec-governed harnesses, spec-governed generators, inert whole-payload
  fixtures, or curated eval cases." Line 16: "NEVER: a test file declaration, variable
  binding, fixture parameter, property-generated parameter, or renamed constant changes
  ownership." This is the decision correction (2)'s exemplars contradict.
- `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`
  — harnesses manage context/resources and property-run configuration; they do **not** own
  domain truth or replace the behavior under test. The DI exemplar defect (below) makes a
  harness own the assertion, which this PDR forbids.
- `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` — five-type
  taxonomy; `[audit]` verdicts run in an isolated verifier context. Constrains how the
  auditors are invoked, not their content.

## The two exemplar defects in typescript-test-standards (src/plugins/typescript/skills/typescript-test-standards/SKILL.md)

Verify line numbers against the current file before editing — the pre-compaction reading
was line ~168–176 (`<dependency_injection>`) and ~183–188 (`<property_based_testing>`);
the file was not in the PR 459 base delta but re-confirm.

- `<dependency_injection>` exemplar: the executed test body is a single harness call
  (`await assertPaymentGatewayRecordsCharge(PaymentProcessor);`) with **zero `expect` in
  the test file** — the harness owns the assertion. Contradicts test-verification.md:12,16
  and 15-test-infrastructure.pdr.md (harness owns resources, not truth). Correct so the
  test file owns the assertion flow; the harness provides the resource/double only.
- `<property_based_testing>` exemplars: every required pattern
  (`assertProperty(parserRoundtripProperty())`) pre-builds the predicate **outside** the
  test file. The property predicate is assertion flow and belongs in the executed test; the
  generator/harness supplies the domain and run configuration. Correct accordingly.
- Line ~203 ("Executed TypeScript test files do not declare `const`, `let`, or `var`
  bindings, framework fixture parameters, or property-generated parameters") is
  absolute-sounding and reads as banning assertion-flow locals — reconcile with
  test-verification.md:16, which bans *ownership laundering*, not all bindings.

## Author/judge asymmetry (the measured root cause)

An agent writing a TypeScript test cannot see the criteria it will be judged by:
`audit-typescript-tests` loads `spec-tree:audit-tests` (the rulebook); `test-typescript`
does not. Correct model: the **standard** owns every rule, every list, and the criterion
for determining the rule is met; author skills and auditor skills both reference the same
standard. Re-measure `test-typescript`'s loaded skill set after the `/test`→`/verify`
relegation that PR 459 landed (`test/SKILL.md` and `test/references/methodology.md`
changed) before treating the asymmetry numbers as current.

## Coupling-taxonomy drift

`audit-typescript-tests` restates a 6-row coupling table against the 9 rows in
`/audit-tests`, silently dropping **Laundered indirect**, **None**, and **Prose-coupling**.
Under the corrected model the table is not restated at all — the auditor refers to the
standard's list.

## Auditor-as-loop target shape (~70–90 lines, from ~448)

```text
<objective> <constraints> <prerequisites> <audit_scope>
<audit_loop>
  For each rule in the referenced standard:
    1. applicable to this subject? -> no: NOT_APPLICABLE + why
    2. judge by the rule's own stated criterion
    3. emit PASS | FAIL with rule address, artifact, evidence
  Then delegate language-neutral evidence properties to /audit-tests; merge by name.
<verdict_format> <success_criteria>
```

The auditor MUST NOT enumerate a list of its own (a second inventory drifts). Rule
addressing follows the spec-tree-native positional form (containing skill + section +
sibling-local index), not a flat global id registry — a tombstone/global-id scheme was
retracted this session as contrary to `<ordering_model>` and `<declarations>`.

## Touched-file debt (fix-now on every node this slice edits)

Every node spec above carries `([review])`, the legacy spelling of `([audit])`. Product
ISSUES.md tracks the tree-wide migration; per touched-file debt, migrate `[review]` →
`[audit]` (text unchanged, tag only) on each node the slice edits, gating each with the
spec auditor. Do not defer this for edited nodes.

Also in scope when their files are touched (from this node's ISSUES.md):

- "Top-Level Specs Restate Methodology" — the three top-level child specs use generic
  methodology-layer compliance assertions; rewrite to TypeScript-specific product truth
  referencing the shared methodology skill/PDR.
- "[eval] Coverage Beyond the Slice" — candidates for `[review]`→`[eval]` migration as
  `audit-typescript-tests` gains structural-verdict output the grader can match.

## Dependency — do not start before this clears

The slice delegates TypeScript standards *to* a shared methodology surface still being
finalized in a sibling worktree. Merge order: plugins-n (PR 459, MERGED) → plugins-e →
plugins-c. Start only on plugins-e's merge, which carries:

- final section list of `src/plugins/spec-tree/skills/test-evidence-standards/SKILL.md`
  (what the TypeScript standards reference);
- whether it ships explicit rule addresses (so the auditor's `for each rule` loop can cite
  them) or prose-only;
- settled state of `test/SKILL.md`, `test/references/methodology.md`, `evidence.md`, and
  `test-typescript/SKILL.md` after the `/test`→`/verify` relegation.

## Revisit condition

Replace this plan with the executed slice once plugins-e merges and
`test-evidence-standards` is on `origin/main`. Re-run `/contextualize` on this node after
that merge — the delegation target and the `/test` skill will have changed.

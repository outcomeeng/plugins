# TypeScript Standards Subtree Issues

## Deferred Decomposition

The reverse-engineering of the three TypeScript standardizing skills into a spec-tree subtree was scoped to a single vertical slice: the eval-harness enabler plus one `[eval]` assertion against the `NEVER shared test-owned constant bags` rule. The following decompositions remain to be authored:

- `spx/43-typescript.enabler/25-typescript-standards.enabler/21-typescript-architecture.enabler/` carries a single top-level spec and has no sub-enablers. Candidate sub-enablers correspond to the TypeScript-specific sections of `plugins/typescript/skills/typescript-architecture-standards/SKILL.md` — DI patterns, level-context-for-TypeScript, anti-patterns. Methodology-restating sections (`adr_sections`, `atemporal_voice`) belong in a Spec Tree PDR, not under this subtree (see `spx/43-typescript.enabler/ISSUES.md`).
- `spx/43-typescript.enabler/25-typescript-standards.enabler/29-typescript-code.enabler/` carries a single top-level spec and has no sub-enablers. Candidate sub-enablers correspond to the sections of `plugins/typescript/skills/typescript-standards/SKILL.md` — type-safety, production-constants, source-of-truth-registries, script-boundaries, error-handling, security, code-hygiene, import-hygiene.
- `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/` has four sub-enablers. Missing concerns from `plugins/typescript/skills/typescript-test-standards/SKILL.md`: file-naming (`<subject>.<evidence>.<level>[.<runner>].test.ts`), level-tooling (vitest, playwright), property-based-testing patterns (fast-check), playwright-request-context.

## Top-Level Specs Restate Methodology

The three top-level specs in this subtree (`typescript-architecture.md`, `typescript-tests.md`, `typescript.md` under `29-typescript-code.enabler`) currently use generic compliance assertions that describe what the skills do at the methodology layer. They should be rewritten to assert only TypeScript-specific product truth — what TypeScript code, ADRs, and tests in marketplace consumers must satisfy — and reference the Spec Tree PDR (once authored) for methodology concerns.

## [eval] Coverage Beyond the Slice

The shared-test-owned-constant-bag rule under `32-test-data-ownership.enabler/` is the only assertion across this subtree carrying `[eval]` evidence; every other compliance assertion now carries `[audit]`. As the audit-typescript-tests skill gains structural-verdict output the eval grader can match against, additional rules become candidates for `[eval]` migration — particularly assertions whose violation pattern is unambiguous in a single test file (e.g., fixture imports, generator-only `fc.constant` wrappers).

## Eval Runner CI Gate

The l3 eval test under `32-test-data-ownership.enabler/tests/` is skipped unless `OUTCOMEENG_RUN_L3_EVALS=1` is set in the environment. A CI workflow that runs l3 evals on a scheduled cadence (not per-PR) needs to be configured separately — the harness exits 0 on a passing suite, so the integration is a matter of selecting cases and gating cost.

## The shipped TypeScript test examples move assertions into the harness

The shared `<predicate_seam>` in `test-evidence-standards` requires every assertion API call to be lexically visible in the linked test, and its `<assertion_type_litmus>` requires a property's invariant to remain in the linked test while the generator owns the domain and the harness keeps the seed, the run count and the replay diagnostics. `25-typescript-tests.enabler/43-test-infrastructure-auditing.enabler/test-infrastructure-auditing.md` already forbids an imported harness that itself calls `expect`, an assertion API or a matcher. The shipped examples in `src/plugins/typescript/skills/typescript-test-standards` contradict both. The Rust plugin was corrected to the right shape first, and `spx/43-rust.enabler/ISSUES.md` records its worked examples as the reference.

Twenty example sites fall in three classes:

- Thirteen bare delegations, `await assertX(...)` as the whole test body with no `expect`: `references/exception-implementations.md` lines 15, 19, 36, 42, 62, 68, 85 and 102, `references/l1-patterns.md` line 53, `references/l2-patterns.md` lines 13 and 17, `levels/l1-local-deterministic.md` line 73 and `levels/l2-local-infrastructure.md` line 35.
- Six property-run delegations, `assertProperty(...)` moving the whole run into the harness: `SKILL.md` lines 204 to 207 (the four-row pattern table), `references/l1-patterns.md` line 20 and `levels/l1-local-deterministic.md` line 54.
- One naming defect, `levels/l3-remote-credentialed.md` line 34, which keeps `expect` in the test and reads `await expect(assertSignedStripeFixtureAccepted()).resolves.toMatchObject(...)`. The seam holds; the helper's name asserts something it does not do.

`audit-typescript-tests` line 132 repeats the same claim, that the invariant lives in the imported property harness.

**Settlement condition.** The first two classes put the assertion flow in the test and leave the harness the resource, the double and the run configuration; the third renames the helper; and `audit-typescript-tests` states the invariant in the linked test. The change is skill content only, with no spec assertion changing, and it passes the typed skill auditor.

**Evidence.** `grep -rn 'assertProperty\|await assert' src/plugins/typescript/skills/typescript-test-standards` lists the sites.

## Four reference files over 100 lines carry no table of contents

`/skill-standards` `<progressive_disclosure>` requires a table of contents at the top of every reference file over 100 lines, so partial reads still see the full scope. Four files in this node's skills exceed the threshold without one: `src/plugins/typescript/skills/architect-typescript/references/typescript-principles.md` (144 lines), `src/plugins/typescript/skills/code-typescript/references/outcome-engineering-patterns.md` (138), `src/plugins/typescript/skills/code-typescript/references/vocabulary-registry-pattern.md` (116) and `src/plugins/typescript/skills/typescript-test-standards/references/exception-implementations.md` (109).

**Settlement condition.** Each file opens with a table of contents in the form its surrounding skill uses, listing every top-level section, and `instructions:skill-auditor` approves each affected skill. The marketplace carries the same gap in other plugins, each recorded in its own node.

# TypeScript Standards Subtree Issues

## Deferred Decomposition

The reverse-engineering of the three TypeScript standardizing skills into a spec-tree subtree was scoped to a single vertical slice: the eval-harness enabler plus one `[eval]` assertion against the `NEVER shared test-owned constant bags` rule. The following decompositions remain to be authored:

- `spx/43-typescript.enabler/25-typescript-standards.enabler/21-typescript-architecture.enabler/` carries a single top-level spec and has no sub-enablers. Candidate sub-enablers correspond to the TypeScript-specific sections of `plugins/typescript/skills/standardizing-typescript-architecture/SKILL.md` — DI patterns, level-context-for-TypeScript, anti-patterns. Methodology-restating sections (`adr_sections`, `atemporal_voice`) belong in a Spec Tree PDR, not under this subtree (see `spx/43-typescript.enabler/ISSUES.md`).
- `spx/43-typescript.enabler/25-typescript-standards.enabler/29-typescript-code.enabler/` carries a single top-level spec and has no sub-enablers. Candidate sub-enablers correspond to the sections of `plugins/typescript/skills/standardizing-typescript/SKILL.md` — type-safety, production-constants, source-of-truth-registries, script-boundaries, error-handling, security, code-hygiene, import-hygiene.
- `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/` has four sub-enablers. Missing concerns from `plugins/typescript/skills/standardizing-typescript-tests/SKILL.md`: file-naming (`<subject>.<evidence>.<level>[.<runner>].test.ts`), level-tooling (vitest, playwright), property-based-testing patterns (fast-check), playwright-request-context.

## Top-Level Specs Restate Methodology

The three top-level specs in this subtree (`typescript-architecture.md`, `typescript-tests.md`, `typescript.md` under `29-typescript-code.enabler`) currently use generic compliance assertions that describe what the skills do at the methodology layer. They should be rewritten to assert only TypeScript-specific product truth — what TypeScript code, ADRs, and tests in marketplace consumers must satisfy — and reference the Spec Tree PDR (once authored) for methodology concerns.

## [eval] Coverage Beyond the Slice

The shared-test-owned-constant-bag rule under `32-test-data-ownership.enabler/` is the only assertion currently carrying `[eval]` evidence. Every other compliance assertion across this subtree remains `[review]`. As the auditing-typescript-tests skill is rebuilt to emit XML verdicts per `spx/15-audit-verdict-format.pdr.md`, additional rules become candidates for `[eval]` migration — particularly assertions whose violation pattern is unambiguous in a single test file (e.g., fixture imports, generator-only `fc.constant` wrappers).

## Eval Runner CI Gate

The l3 eval test under `32-test-data-ownership.enabler/tests/` is skipped unless `OUTCOMEENG_RUN_L3_EVALS=1` is set in the environment. A CI workflow that runs l3 evals on a scheduled cadence (not per-PR) needs to be configured separately — the harness exits 0 on a passing suite, so the integration is a matter of selecting cases and gating cost.

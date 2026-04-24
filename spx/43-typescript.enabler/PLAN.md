# PLAN — TypeScript enablers for standards and test standards

## Why

TypeScript plugin ships `/standardizing-typescript` (code standards) and `/standardizing-typescript-tests` (test standards + ESLint rules) but neither is declared in the spec tree. The ESLint rules carry noise (long allow list, size heuristics, protocol exceptions) that dilutes the literal rule. Production code has no guidance on defining constant objects, so agents either hardcode literals in tests or build constant bags that launder values.

## Scope

Two child enablers, authored under `spx/43-typescript.enabler/`.

### 1. `NN-standardizing-typescript.enabler/` — TypeScript code standards

- **Constant objects.** `const NAME = { KEY: "value", ... } as const` plus `type NameValue = (typeof NAME)[keyof typeof NAME]`. Production defines, uses at least once internally, and exports. One definition, single point of change.
- **No enums.** Rationale: runtime cost, declaration-merging with namespaces, opaque compile output, no narrowing with string literal types. `as const` object literals cover every use case enums address, with zero runtime overhead and full type narrowing.
- **No re-export of library constants.** Production imports from `node:*` or the platform/library origin (Node stdlib, Playwright, Zod, etc.). Tests import from the same origin. Production is not a constants-repackaging layer.
- **Constant-object test.** At least one Scenario asserting the pattern compiles to `as const` literal types. At least one Compliance rule rejecting enum declarations.

### 2. `NN-standardizing-typescript-tests.enabler/` — TypeScript test standards

- **Number allow list: `{-1, 0, 1, 2}`.** Already matches `allowedRawNumbers`. Declare as an assertion. Any other number in a test file flagged unless imported from a library origin, a production-owned constant object, or generated (fast-check / faker / harness function).
- **String allow list: `{""}` plus descriptive callsites.** Declare as an assertion. Descriptive callsites (`it`, `describe`, `test`, `test.each`, `expect` message arg) already in `TEST_STRING_POLICY`. Drop every other exception.
- **Strip `literal-signal.ts`.** Remove `COMMON_LITERAL_ALLOWLIST` (~60 entries covering HTTP methods, MIME types, encodings, CSS keywords, JS type names, Node builtins). Remove `MIN_STRING_LENGTH` and `MIN_NUMBER_DIGITS`. `isMeaningfulString(v) ⇔ v.length > 0`. `isMeaningfulNumber(n) ⇔ ![-1, 0, 1, 2].includes(n)`. If nothing is left shared between rules, fold into the rule files and delete `literal-signal.ts`.
- **Strip `test-string-policy.ts`.** Keep `descriptiveCallsites`. Delete `protocolStringExceptions` and its ARIA, Playwright load-state, DOM attribute lists. Consumers who need protocol exceptions extend via `eslint.audit.config.ts`.
- **Remediation documentation.** The standardizing skill tells agents the four legal resolutions: library-origin import, production-owned constant object (per `/standardizing-typescript`), generator, descriptive-callsite inline. Fixtures explicitly banned.

## Out of scope

- The generic literal rule itself — lives in `spx/21-spec-tree.enabler/32-evidence.enabler/32-test-auditing.enabler/`.
- Python equivalent — lives in `spx/43-python.enabler/PLAN.md`.
- Testability gate schema change — lives in `spx/21-spec-tree.enabler/32-evidence.enabler/43-audit-verdict-schema.enabler/PLAN.md`.

## Done when

- Both child enabler nodes exist with specs, tests, and implementation code either passing or cleanly marked `spx/EXCLUDE`.
- `plugins/typescript/skills/standardizing-typescript/SKILL.md` teaches the constant-object and no-re-export rules.
- `plugins/typescript/skills/standardizing-typescript-tests/SKILL.md` `<test_data_policy>` and `<lint_enforcement>` sections reflect the short allow lists and the four-resolution pattern.
- `plugins/typescript/skills/standardizing-typescript-tests/eslint-rules/` reduced: short allow lists only, no protocol exceptions, no size heuristics.
- `tests/` directories under the new enablers exercise the rules against fixture test files.

## Origin

Conversation on 2026-04-24. Started from a Codex plugin-cache diff and evolved into the realization that the allow list should be short, the positive pattern is a production-owned constant object shared with tests, and TypeScript needs explicit no-enum guidance because agents reach for enums when told to group constants.

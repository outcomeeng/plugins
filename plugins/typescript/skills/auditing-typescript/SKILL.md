---
name: auditing-typescript
description: >-
  ALWAYS invoke this skill when auditing code for TypeScript or after writing code.
  NEVER modify a spec to match code without auditing the code first.
allowed-tools: Read, Bash, Glob, Grep
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript/SKILL.md"`

<objective>

Adversarial code review through comprehension. Find design flaws that automated tools cannot catch. Produce a structured verdict -- not code changes.

This skill is read-only. It produces verdicts, not commits or fixes.

**Test evidence quality is audited by `/auditing-typescript-tests`.** This skill audits implementation code, not test code. If test files are in scope, delegate to `/auditing-typescript-tests`.

**Before reviewing code, read `/standardizing-typescript`.** After that, check for `spx/local/typescript.md` at the repository root. Read that file if it exists and apply it as the repo-local specialization.

</objective>

<quick_start>

1. Read `/standardizing-typescript`, then `spx/local/typescript.md` if present, then `/testing` for methodology + `/testing-typescript` for TypeScript patterns
2. Load project config: `CLAUDE.md`, `tsconfig.json`, `package.json` (Phase 0)
3. Run automated gates -- project validation command (Phase 1, blocking)
4. Run tests -- verify all pass (Phase 2, blocking)
5. **Comprehend every function** -- predict, verify, investigate (Phase 3)
6. Check ADR/PDR compliance (Phase 4)
7. Produce structured verdict: APPROVED or REJECTED

</quick_start>

<essential_principles>

**Trust automated gates, then comprehend.**

Phases 1-2 are mechanical prerequisites. If they fail, stop -- REJECTED. If they pass, do NOT re-check what linters and tests already verified. Your time is for Phase 3.

**Comprehension is the core value.**

Automated tools catch syntax errors, type mismatches, and lint violations. You catch: functions that do more than their name says, dead parameters required by no interface, IO tangled with logic, and designs that will break under change. The predict/verify protocol (Phase 3) is how you find these.

**Test evidence is not your concern.**

`/auditing-typescript-tests` evaluates whether tests provide genuine evidence using the 4-property model (coupling, falsifiability, alignment, coverage). This skill verifies tests PASS, not whether they have evidentiary value. Do not duplicate that work.

**Binary verdict, no caveats.**

APPROVED means every concern passes. REJECTED means at least one fails. APPROVED output contains no notes, warnings, or suggestions sections.

</essential_principles>

<process>

Execute phases IN ORDER. Do not skip.

**Phase 0: Scope and Project Config**

1. Determine target files/directories
2. Read `CLAUDE.md`/`README.md` for validation commands and test runners
3. Check `tsconfig.json`, `package.json` for tool configurations

**Phase 1: Automated Gates** (blocking)

Run the project's validation command. Catches everything linters handle: type safety, naming, magic numbers, unused imports, security rules.

If the project lacks its own linter configs, use the reference configs in `${CLAUDE_SKILL_DIR}/rules/`:

| File                   | Purpose                                      |
| ---------------------- | -------------------------------------------- |
| `tsconfig.strict.json` | Strict TypeScript compiler options           |
| `eslint.config.js`     | ESLint strict + security rules               |
| `semgrep_sec.yaml`     | Semgrep security patterns (CWE-78/89/94/798) |

Non-zero exit = REJECTED. Do not proceed.

Do NOT manually re-check what linters catch. If the project's linters are properly configured per `/standardizing-typescript`, they handle type annotations, naming, unused imports, commented-out code, and security rules.

**Note**: Some rules require manual verification during Phase 3 -- deep relative imports, unqualified `any`, `@ts-ignore` without justification.

**Phase 2: Test Execution** (blocking)

Run the full test suite. Use the project's test runner from `CLAUDE.md`.

If tests require infrastructure (databases, Docker), attempt to provision it. Do not skip tests because infrastructure "isn't running" -- try to start it first.

ANY test failure = REJECTED. Do not proceed.

**Phase 3: Code Comprehension**

Read every file. Understand it. Question it. Do NOT skim, sample, or check boxes.

**3.1 Per-Function Protocol**

For each function/method:

1. **Read name and signature only** -- name, parameters, return type
2. **Predict** what it does in one sentence
3. **Read the body** -- validate your prediction
4. **Investigate surprises:**

| Surprise                               | What it suggests                                   |
| -------------------------------------- | -------------------------------------------------- |
| Parameter never used in body           | Dead parameter -- required by interface, or remove |
| Does more than name says               | SRP violation or misleading name                   |
| Does less than name says               | Name overpromises or logic is incomplete           |
| Variable assigned but never read       | Dead code or unfinished logic                      |
| Code path that can never execute       | Dead branch given calling context                  |
| Return value contradicts the type hint | Logic error or wrong return type                   |

Prediction matched? Move on. Surprise? Document it with `file:line`.

**3.2 Design Evaluation**

For the codebase as a whole:

- **IO vs logic separation** -- Can core logic be tested without IO? Tangled computation and side effects need factoring.
- **Dependency injection** -- External dependencies injected via parameters, or imported as globals?
- **Single responsibility** -- Each module/class does one thing? Each function does one thing?
- **Error quality** -- Errors include what failed and with what input?
- **Domain exceptions** -- Custom exceptions for domain errors, or everything generic `Error`?

**3.3 Import Evaluation**

Evaluate import structure using the same vocabulary as `/auditing-typescript-tests`:

| Import pattern                                   | Classification                  |
| ------------------------------------------------ | ------------------------------- |
| `import { describe, expect } from "vitest"`      | Framework -- not reviewed       |
| `import { z } from "zod"`                        | Library -- not reviewed         |
| `import type { Config } from "../src/config"`    | Type-only -- erased at runtime  |
| `import { parseConfig } from "../src/config"`    | Codebase (production) -- review |
| `import { parseConfig } from "@/config"`         | Codebase (alias) -- review      |
| `import { TestHarness } from "@testing/helpers"` | Codebase (test infra) -- review |

**Import depth rules:**

| Depth     | Example        | Verdict                          |
| --------- | -------------- | -------------------------------- |
| Same dir  | `./utils`      | OK -- module-internal            |
| 1 level   | `../types`     | Review -- truly module-internal? |
| 2+ levels | `../../config` | REJECT -- use path alias         |

For stable locations (`lib/`, `tests/helpers/`, `shared/`), path aliases are mandatory regardless of depth.

See `${CLAUDE_SKILL_DIR}/references/false-positive-handling.md` for application context when evaluating security and linter suppression comments.

**Phase 4: ADR/PDR Compliance**

Find applicable ADRs/PDRs in the spec hierarchy (`*.adr.md`, `*.pdr.md`). Verify each constraint is followed. Undocumented deviations = REJECTED. If the project has no spec hierarchy, this concern is N/A.

| Decision Record Constraint           | Violation Example                   | Verdict  |
| ------------------------------------ | ----------------------------------- | -------- |
| "Use dependency injection" (ADR)     | Direct imports of external services | REJECTED |
| "`l1` tests for logic" (ADR)         | `l1` tests hitting network          | REJECTED |
| "No class components" (ADR)          | React class component added         | REJECTED |
| "Lifecycle is Draft→Published" (PDR) | Added hidden `Archived` state       | REJECTED |

</process>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved code that passed linters but had a design flaw.** The auditor trusted Phase 1 output and skimmed Phase 3. The code had a function named `validateConfig` that also wrote the config file -- SRP violation hidden behind a reasonable name. The predict/verify protocol would have caught it: "Given the name, I predict this validates. But the body also calls `writeFileSync`. Surprise."

**Rejected code for a false positive.** The auditor flagged a parameter as "dead code" because it wasn't used in the function body. The parameter was required by a `CommandHandler` interface contract -- other implementations used it. Before flagging dead parameters, check if the function implements an interface or Protocol.

**Tried to evaluate test evidence instead of delegating.** The auditor found `vi.fn()` in tests and spent time analyzing whether it broke coupling. That's `/auditing-typescript-tests`' job. This auditor should have verified tests PASS (Phase 2) and moved on to comprehending the implementation code.

**Distracted by style while missing a logic bug.** The auditor spent review time on naming conventions, import ordering, and JSDoc completeness. Meanwhile, a branch condition was inverted -- `if (isValid)` should have been `if (!isValid)`. Comprehension (understanding what the code does) must come before style. Style is the linter's job.

**Accepted code with tangled IO.** A `processOrders` function both computed order totals AND sent confirmation emails. Tests passed and types were correct. But the function was untestable without an email server -- IO and logic were tangled. The design evaluation (3.2) would have caught it: "Can core logic be tested without IO? No."

</failure_modes>

<output_format>

````markdown
# CODE REVIEW

**Decision:** [APPROVED | REJECTED]

## Verdict

| # | Concern                | Status            | Detail            |
| - | ---------------------- | ----------------- | ----------------- |
| 1 | Automated gates        | {PASS/REJECT}     | {one-line detail} |
| 2 | Test execution         | {PASS/REJECT}     | {one-line detail} |
| 3 | Function comprehension | {PASS/REJECT}     | {one-line detail} |
| 4 | Design coherence       | {PASS/REJECT}     | {one-line detail} |
| 5 | Import structure       | {PASS/REJECT/N/A} | {one-line detail} |
| 6 | ADR/PDR compliance     | {PASS/REJECT/N/A} | {one-line detail} |

---

## Findings (REJECTED only)

### {Finding name}

**Where:** {file:line or section}
**Concern:** {which concern from verdict table}
**Why this fails:** {direct explanation}

**Correct approach:**

```typescript
{What the code should look like}
```

---

{Repeat for each finding}

---

## Required Changes (REJECTED only)

{Concise list of what must change}

---

{If REJECTED: "Fix issues and resubmit for review."}
{If APPROVED: "Code meets standards."}
````

</output_format>

<what_to_avoid>

- Do NOT re-check linter concerns (Phase 1 handles those)
- Do NOT evaluate test evidence quality (delegate to `/auditing-typescript-tests`)
- Do NOT commit or modify code (this skill is read-only)
- Do NOT approve with caveats (binary verdict only)
- Do NOT reject for code style when comprehension found no design flaws

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-review.md` for complete APPROVED and REJECTED examples showing all concern types.

</example_review>

<success_criteria>

Review is complete when:

- [ ] Project validation command run (Phase 1)
- [ ] Test suite run (Phase 2)
- [ ] Every function comprehended via predict/verify protocol (Phase 3)
- [ ] Design evaluated: IO/logic, DI, SRP, error quality (Phase 3)
- [ ] Import structure checked (Phase 3)
- [ ] ADR/PDR compliance verified (Phase 4)
- [ ] Structured verdict table with per-concern status
- [ ] For REJECT: findings with concern, explanation, and correct approach
- [ ] Decision clearly stated (APPROVED/REJECTED)

</success_criteria>

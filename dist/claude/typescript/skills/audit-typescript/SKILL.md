---
name: audit-typescript
description: >-
  TypeScript implementation-code audit methodology — design flaws and ADR compliance — composed by a generic auditor agent for the TypeScript files in scope.
  Reached only through a dispatched auditor agent, never the main conversation.
allowed-tools: Read, Bash, Glob, Grep, Skill
---

Invoke the `typescript:typescript-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<dispatch_gate>

This audit runs inside a dispatched auditor's verifier context — a generic auditor agent (`auditor`, `audit-orchestrator`, `pr-reviewer`, or `pr-review-orchestrator`) composing this skill for the TypeScript files in scope — isolated from the author context that produced the work under audit. When this skill loads in the author/main conversation rather than inside a dispatched auditor agent, STOP — the audit must run in that verifier context. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

A verdict on TypeScript implementation code — APPROVED, or REJECTED with each finding naming the design flaw, the violated rule, and the evidence.

</objective>

<repo_local_overlay>
Standards are pre-loaded above. Check for `spx/local/typescript.md` at the repository root. Read it if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<essential_principles>

**Comprehension is the whole job.**

This audit reads and judges TypeScript implementation code; it runs no deterministic verification of its own. The main agent brings the project's linters, type-checker, and tests to passing on the changeset before dispatching this audit, and CI re-runs them over the whole repository — so do NOT run or re-check what those gates already verified. Spend the whole audit on comprehension.

**Comprehension is the core value.**

Automated tools catch syntax errors, type mismatches, and lint violations. Claude catches: functions that do more than their name says, dead parameters required by no interface, IO tangled with logic, and designs that will break under change. The predict/verify protocol (Phase 1) is how these surface.

**Test evidence is out of scope.**

`/audit-typescript-tests` evaluates whether tests provide genuine evidence using the 4-property model (coupling, falsifiability, alignment, coverage). This skill judges implementation design, not test evidence — and it does not run the test suite; the main agent already passed it before dispatch. Do not duplicate that work.

**Binary verdict, no caveats.**

APPROVED means every concern passes. REJECTED means at least one fails. APPROVED output contains no notes, warnings, or suggestions sections.

</essential_principles>

<audit_workflow>

Execute phases IN ORDER. Do not skip. This audit runs no deterministic verification — no linter, type-checker, or test run. The main agent brought the project's validation and tests to passing on the changeset before dispatching this audit, and CI re-runs them over the whole repository; re-running them here only re-pays a cost already paid.

**Phase 0: Scope and Product Config**

1. Determine target files/directories
2. Check `tsconfig.json`, `package.json`, and `CLAUDE.md`/`README.md` for tool and project configuration that informs comprehension (lint, type-check, test settings; naming conventions) — read for context, never to run a gate. The linters already handled type annotations, naming, unused imports, commented-out code, and security rules; comprehension covers what they cannot — deep relative imports, unqualified `any`, and `@ts-ignore` without justification.

**Phase 1: Code Comprehension**

Read every file. Understand it. Question it. Do NOT skim, sample, or check boxes.

**1.1 Per-Function Protocol**

For each function/method:

1. **Read name and signature only** -- name, parameters, return type
2. **Predict** what it does in one sentence
3. **Read the body** -- validate the prediction
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

**1.2 Design Evaluation**

For the codebase as a whole:

- **IO vs logic separation** -- Can core logic be tested without IO? Tangled computation and side effects need factoring.
- **Dependency injection** -- External dependencies injected via parameters, or imported as globals?
- **Single responsibility** -- Each module/class does one thing? Each function does one thing?
- **Error quality** -- Errors include what failed and with what input?
- **Domain exceptions** -- Custom exceptions for domain errors, or everything generic `Error`?

**1.3 Import Evaluation**

Evaluate import structure using the same vocabulary as `/audit-typescript-tests`:

| Import pattern                                     | Classification                     |
| -------------------------------------------------- | ---------------------------------- |
| `import { describe, expect } from "vitest"`        | Framework -- not reviewed          |
| `import { z } from "zod"`                          | Library -- not reviewed            |
| `import type { Config } from "../src/config"`      | Type-only -- erased at runtime     |
| `import { parseConfig } from "../src/config"`      | Codebase (production) -- review    |
| `import { parseConfig } from "@/config"`           | Codebase (alias) -- review         |
| `import { TestHarness } from "@testing/harnesses"` | Test-only infrastructure -- review |

**Import depth rules:**

| Depth     | Example        | Verdict                          |
| --------- | -------------- | -------------------------------- |
| Same dir  | `./utils`      | OK -- module-internal            |
| 1 level   | `../types`     | Review -- truly module-internal? |
| 2+ levels | `../../config` | REJECT -- use path alias         |

For stable production locations (`lib/`, `shared/`), path aliases are mandatory regardless of depth. For tests and test-infrastructure modules, `@testing/harnesses/*` and `@testing/generators/*` are mandatory; product modules must not import `@testing/*`.

See `${CLAUDE_SKILL_DIR}/references/false-positive-handling.md` for application context when evaluating security and linter suppression comments.

**Phase 2: ADR/PDR Compliance**

Find applicable ADRs/PDRs in the spec hierarchy (`*.adr.md`, `*.pdr.md`). Verify each constraint is followed. Undocumented deviations = REJECTED. If the product has no spec hierarchy, this concern is N/A.

| Decision Record Constraint           | Violation Example                   | Verdict  |
| ------------------------------------ | ----------------------------------- | -------- |
| "Use dependency injection" (ADR)     | Direct imports of external services | REJECTED |
| "`l1` tests for logic" (ADR)         | `l1` tests hitting network          | REJECTED |
| "No class components" (ADR)          | React class component added         | REJECTED |
| "Lifecycle is Draft→Published" (PDR) | Added hidden `Archived` state       | REJECTED |

</audit_workflow>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved code that passed linters but had a design flaw.** Claude trusted the green linters (run by the main agent before dispatch) and skimmed comprehension. The code had a function named `validateConfig` that also wrote the config file -- SRP violation hidden behind a reasonable name. The predict/verify protocol would have caught it: "Given the name, I predict this validates. But the body also calls `writeFileSync`. Surprise."

**Rejected code for a false positive.** Claude flagged a parameter as "dead code" because it wasn't used in the function body. The parameter was required by a `CommandHandler` interface contract -- other implementations used it. Before flagging dead parameters, check if the function implements an interface or Protocol.

**Tried to evaluate test evidence instead of delegating.** Claude found `vi.fn()` in tests and spent time analyzing whether it broke coupling. That's `/audit-typescript-tests`' job, and running the test suite is the main agent's before dispatch — not this audit's. Claude should have moved straight to comprehending the implementation code.

**Distracted by style while missing a logic bug.** Claude spent review time on naming conventions, import ordering, and JSDoc completeness. Meanwhile, a branch condition was inverted -- `if (isValid)` should have been `if (!isValid)`. Comprehension (understanding what the code does) must come before style. Style is the linter's job.

**Accepted code with tangled IO.** A `processOrders` function both computed order totals AND sent confirmation emails. Tests passed and types were correct. But the function was untestable without an email server -- IO and logic were tangled. The design evaluation (1.2) would have caught it: "Can core logic be tested without IO? No."

</failure_modes>

<verdict_format>

Emit the verdict as JSON conforming to the canonical audit-verdict schema consumed by the composing audit workflow. The skill's entire output is the JSON verdict. The composing audit workflow records and renders the verdict through the audit journal path.

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "audit-typescript",
  "target": "<scope-target>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "function-comprehension", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "design-coherence", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "import-structure", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "adr-pdr-compliance", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding carries `file`, `line`, `rule` (the concern name from the verdict table or a specific violation name), `severity: "REJECT"`, and `message` (the one-line "why this fails"). Include correct-approach code samples and required changes directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</verdict_format>

<what_to_avoid>

- Do NOT run or re-check the project's linters, type-checker, or tests — the main agent passed them on the changeset before dispatch, and CI re-runs them over the whole repository
- Do NOT evaluate test evidence quality (delegate to `/audit-typescript-tests`)
- Do NOT commit or modify code (this skill is read-only)
- Do NOT approve with caveats (binary verdict only)
- Do NOT reject for code style when comprehension found no design flaws

</what_to_avoid>

<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-audit.md` for complete APPROVED and REJECTED examples showing all concern types.

</example_review>

<success_criteria>

Review is complete when:

- [ ] Every function comprehended via predict/verify protocol (Phase 1)
- [ ] Design evaluated: IO/logic, DI, SRP, error quality (Phase 1)
- [ ] Import structure checked (Phase 1)
- [ ] ADR/PDR compliance verified (Phase 2)
- [ ] Structured verdict table with per-concern status
- [ ] For REJECT: findings with concern, explanation, and correct approach
- [ ] Decision clearly stated (APPROVED/REJECTED)

</success_criteria>

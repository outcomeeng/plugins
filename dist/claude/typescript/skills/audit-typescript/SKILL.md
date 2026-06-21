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

Adversarial code review through comprehension. Find design flaws that automated tools cannot catch. Produce a structured verdict -- not code changes.

This skill is read-only. It produces verdicts, not commits or fixes.

**Test evidence quality is audited by skill `/audit-typescript-tests`.** This skill audits implementation code, not test code.
Almost every TypeScript file must be covered by tests. Invoke `/audit-typescript-tests` separately as part of the overall auditing workflow.

</objective>

<quick_start>

1. Read `/test` for methodology + `/test-typescript` for TypeScript patterns
2. Load product config: `CLAUDE.md`, `tsconfig.json`, `package.json` (Phase 0)
3. Run automated gates -- product validation command (Phase 1, blocking)
4. Run tests -- verify all pass (Phase 2, blocking)
5. **Comprehend every function** -- predict, verify, investigate (Phase 3)
6. Check ADR/PDR compliance (Phase 4)
7. Produce structured verdict: APPROVED or REJECTED

</quick_start>

<repo_local_overlay>
Standards are pre-loaded above. Check for `spx/local/typescript.md` at the repository root. Read it if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<essential_principles>

**Trust automated gates, then comprehend.**

Phases 1-2 are mechanical prerequisites. If they fail, stop -- REJECTED. If they pass, do NOT re-check what linters and tests already verified. Spend the audit's time on Phase 3.

**Comprehension is the core value.**

Automated tools catch syntax errors, type mismatches, and lint violations. Claude catches: functions that do more than their name says, dead parameters required by no interface, IO tangled with logic, and designs that will break under change. The predict/verify protocol (Phase 3) is how these surface.

**Test evidence is out of scope.**

`/audit-typescript-tests` evaluates whether tests provide genuine evidence using the 4-property model (coupling, falsifiability, alignment, coverage). This skill verifies tests PASS, not whether they have evidentiary value. Do not duplicate that work.

**Binary verdict, no caveats.**

APPROVED means every concern passes. REJECTED means at least one fails. APPROVED output contains no notes, warnings, or suggestions sections.

</essential_principles>

<process>

Execute phases IN ORDER. Do not skip.

**Phase 0: Scope and Product Config**

1. Determine target files/directories
2. Read `CLAUDE.md`/`README.md` for validation commands and test runners
3. Check `tsconfig.json`, `package.json` for tool configurations

**Phase 1: Automated Gates** (blocking)

Run the product's validation command. Catches everything linters handle: type safety, naming, magic numbers, unused imports, security rules.

Non-zero exit = REJECTED. Do not proceed.

Do NOT manually re-check what linters catch. If the product's linters are properly configured per `/typescript-standards`, they handle type annotations, naming, unused imports, commented-out code, and security rules.

**Note**: Some rules require manual verification during Phase 3 -- deep relative imports, unqualified `any`, `@ts-ignore` without justification.

**Phase 2: Test Execution** (blocking)

Run the full test suite. Use the product's test runner from `CLAUDE.md`.

If tests require infrastructure (databases, Docker), attempt to provision it. Do not skip tests because infrastructure "isn't running" -- try to start it first.

ANY test failure = REJECTED. Do not proceed.

**Phase 3: Code Comprehension**

Read every file. Understand it. Question it. Do NOT skim, sample, or check boxes.

**3.1 Per-Function Protocol**

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

**3.2 Design Evaluation**

For the codebase as a whole:

- **IO vs logic separation** -- Can core logic be tested without IO? Tangled computation and side effects need factoring.
- **Dependency injection** -- External dependencies injected via parameters, or imported as globals?
- **Single responsibility** -- Each module/class does one thing? Each function does one thing?
- **Error quality** -- Errors include what failed and with what input?
- **Domain exceptions** -- Custom exceptions for domain errors, or everything generic `Error`?

**3.3 Import Evaluation**

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

**Phase 4: ADR/PDR Compliance**

Find applicable ADRs/PDRs in the spec hierarchy (`*.adr.md`, `*.pdr.md`). Verify each constraint is followed. Undocumented deviations = REJECTED. If the product has no spec hierarchy, this concern is N/A.

| Decision Record Constraint           | Violation Example                   | Verdict  |
| ------------------------------------ | ----------------------------------- | -------- |
| "Use dependency injection" (ADR)     | Direct imports of external services | REJECTED |
| "`l1` tests for logic" (ADR)         | `l1` tests hitting network          | REJECTED |
| "No class components" (ADR)          | React class component added         | REJECTED |
| "Lifecycle is Draft→Published" (PDR) | Added hidden `Archived` state       | REJECTED |

</process>

<failure_modes>

These are real failures from past audits. Study them to avoid repeating them.

**Approved code that passed linters but had a design flaw.** Claude trusted Phase 1 output and skimmed Phase 3. The code had a function named `validateConfig` that also wrote the config file -- SRP violation hidden behind a reasonable name. The predict/verify protocol would have caught it: "Given the name, I predict this validates. But the body also calls `writeFileSync`. Surprise."

**Rejected code for a false positive.** Claude flagged a parameter as "dead code" because it wasn't used in the function body. The parameter was required by a `CommandHandler` interface contract -- other implementations used it. Before flagging dead parameters, check if the function implements an interface or Protocol.

**Tried to evaluate test evidence instead of delegating.** Claude found `vi.fn()` in tests and spent time analyzing whether it broke coupling. That's `/audit-typescript-tests`' job. Claude should have verified tests PASS (Phase 2) and moved on to comprehending the implementation code.

**Distracted by style while missing a logic bug.** Claude spent review time on naming conventions, import ordering, and JSDoc completeness. Meanwhile, a branch condition was inverted -- `if (isValid)` should have been `if (!isValid)`. Comprehension (understanding what the code does) must come before style. Style is the linter's job.

**Accepted code with tangled IO.** A `processOrders` function both computed order totals AND sent confirmation emails. Tests passed and types were correct. But the function was untestable without an email server -- IO and logic were tangled. The design evaluation (3.2) would have caught it: "Can core logic be tested without IO? No."

</failure_modes>

<output_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "audit-typescript",
  "target": "<scope-target>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "automated-gates", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "test-execution", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "function-comprehension", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "design-coherence", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "import-structure", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "adr-pdr-compliance", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding carries `file`, `line`, `rule` (the concern name from the verdict table or a specific violation name), `severity: "REJECT"`, and `message` (the one-line "why this fails"). Include correct-approach code samples and required changes directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</output_format>

<what_to_avoid>

- Do NOT re-check linter concerns (Phase 1 handles those)
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

- [ ] Product validation command run (Phase 1)
- [ ] Test suite run (Phase 2)
- [ ] Every function comprehended via predict/verify protocol (Phase 3)
- [ ] Design evaluated: IO/logic, DI, SRP, error quality (Phase 3)
- [ ] Import structure checked (Phase 3)
- [ ] ADR/PDR compliance verified (Phase 4)
- [ ] Structured verdict table with per-concern status
- [ ] For REJECT: findings with concern, explanation, and correct approach
- [ ] Decision clearly stated (APPROVED/REJECTED)

</success_criteria>

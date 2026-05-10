---
name: orchestrating-typescript-audit
description: >-
  ALWAYS invoke this skill to review or audit TypeScript code in a single deterministic pass. Produces one binary verdict — APPROVED or REJECTED — covering implementation, test evidence, and architectural compliance. NEVER use this skill to write code.
allowed-tools: Read, Bash, Glob, Grep
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript/SKILL.md" || echo "standardizing-typescript not found — invoke typescript:standardizing-typescript manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript-tests/SKILL.md" || echo "standardizing-typescript-tests not found — invoke typescript:standardizing-typescript-tests manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript-architecture/SKILL.md" || echo "standardizing-typescript-architecture not found — invoke typescript:standardizing-typescript-architecture manually"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. `typescript:standardizing-typescript`
2. `typescript:standardizing-typescript-tests`
3. `typescript:standardizing-typescript-architecture`

</codex_fallback>

<objective>

Run one adversarial, comprehension-based audit over a frozen TypeScript scope and emit a single binary verdict.

This skill is read-only. It produces verdicts — never patches, commits, or prose narratives.

The skill orchestrates three audit surfaces that already exist as standalone skills, but collapses them into one deterministic pass so callers receive a single APPROVED or REJECTED decision:

| Surface             | What is audited                                       | Standalone skill                  |
| ------------------- | ----------------------------------------------------- | --------------------------------- |
| Implementation      | Production code: comprehension, design, IO/logic, DI  | `auditing-typescript`             |
| Test evidence       | Tests as evidence: coupling, falsifiability, oracle   | `auditing-typescript-tests`       |
| Architecture (ADR)  | Decision records governing the scope (when present)   | `auditing-typescript-architecture`|

</objective>

<determinism_contract>

The single most important property of this skill is that **two runs over the same scope produce the same verdict and the same finding set**. Re-running after a fix accepts or rejects the fix; it does not surface unrelated findings.

The four mechanisms that enforce determinism — apply all four, every run:

1. **Frozen scope.** At Phase 0 the scope is captured as an explicit file list and a content hash. Phases 3–5 audit only files in that list. New files discovered by Glob during the run are out of scope.

2. **Frozen concern table.** Every verdict has the same six rows in the same order (see `<verdict_format>`). Concerns are never added, removed, renamed, or reordered to fit a particular audit.

3. **Frozen finding catalog.** Findings are only created from violations of the rules pre-loaded above (`/standardizing-typescript`, `/standardizing-typescript-tests`, `/standardizing-typescript-architecture`) and the predict/verify protocol applied to functions in scope. Style preferences, taste-based critiques, and "could be cleaner" observations are NEVER findings.

4. **Re-run rule.** When a prior verdict for this scope is available (see `<re_run_protocol>`), the audit verifies whether each prior finding is resolved, and only adds new findings that originate from code added or modified since the prior verdict. Untouched code is not re-comprehended for novel issues.

If any mechanism cannot be applied, halt and report the obstacle — do not silently substitute a looser audit.

**This skill is strictly read-only.** It uses `Read`, `Bash` (for `git`, validation, and tests), `Glob`, and `Grep` — never `Write` or `Edit`. The skill does not persist its verdict and does not create the `.spx/audits/typescript/` directory. Re-run determinism depends on the **caller** writing the emitted verdict to a known path; the skill only reads from such a path when one already exists. This keeps the skill compliant with the audit-skill read-only rule and safe to dispatch as a subagent (per `AGENTS.md` line 402, subagents must never create or modify files).

</determinism_contract>

<quick_start>

1. Phase 0: freeze scope, hash it, read any prior verdict the caller has staged
2. Phase 1: run automated gates — non-zero exit is REJECTED, halt
3. Phase 2: run the test suite — any failure is REJECTED, halt
4. Phase 3: comprehend every function in scope using predict/verify
5. Phase 4: audit test evidence for assertions traceable to scope
6. Phase 5: verify ADR/PDR compliance for the scope (or mark N/A)
7. Phase 6: emit the verdict in the canonical format (the caller persists it)

</quick_start>

<essential_principles>

**Trust automated gates, then comprehend.** Phases 1–2 are mechanical prerequisites. If they fail, stop. If they pass, do not re-check what linters and the test runner already verified.

**Comprehension is the value Claude adds.** Linters catch syntax, types, naming, and unused imports. Claude catches functions that do more than their name says, parameters that are dead in every implementation, IO tangled with logic, and oracles that derive expected values from the module under test.

**Binary verdict, no caveats.** APPROVED means every concern passes. REJECTED means at least one fails. APPROVED output is a checklist — not prose, not encouragement, not "great work." See `<output_format>`.

**Read-only.** Never edit code. Never propose patches in the form of a diff. Findings include a corrected snippet, but the calling workflow decides what to do with the verdict.

**Stability over thoroughness.** When two readings of a function are plausible, pick the one that aligns with the function's name and signature and document the assumption. Do not generate new findings on re-run because Claude reread the same code more skeptically.

</essential_principles>

<process>

Execute phases in order. Do not skip. Do not reorder.

<phase number="0" name="scope_and_context">

**Goal:** Lock in exactly what is being audited before reading any code for review.

1. **Determine scope.** The caller provides one of:
   - An explicit file or directory list — use as-is.
   - A git ref or diff range (`HEAD`, `main..HEAD`, a branch name) — expand with `git diff --name-only <range> -- '*.ts' '*.tsx'`.
   - No scope — default to `git diff --name-only HEAD -- '*.ts' '*.tsx'` (uncommitted + staged TypeScript changes). If that returns empty, halt with "no TypeScript scope detected".

2. **Materialize the file list.** Filter to existing files matching `*.ts` or `*.tsx`. Sort lexicographically. This sorted list is the **frozen scope** for this run.

3. **Compute scope hash.** `sha256` over the concatenation of file path + null byte + file content for every file in the frozen scope. Use the first 12 hex characters as the **scope hash**. Implementation:

   ```bash
   { for f in <files-in-sort-order>; do printf '%s\0' "$f"; cat "$f"; done; } | (sha256sum 2>/dev/null || shasum -a 256) | cut -c1-12
   ```

4. **Read prior verdict if staged.** Look for `.spx/audits/typescript/<scope-hash>.md`. If found, read it — see `<re_run_protocol>` for how to use it. If absent, this is a fresh run. The skill never creates this file; it only reads one the calling workflow has placed there from a previous run.

5. **Read project config.** `CLAUDE.md`, `AGENTS.md`, `tsconfig.json`, `package.json`. Identify the canonical validation command (often `pnpm validate`, `npm run validate`, or `just check`) and the canonical test command. If these are not discoverable from project files, halt — do not guess.

6. **Read repo-local overlays.** `spx/local/typescript.md`, `spx/local/typescript-tests.md`, `spx/local/typescript-architecture.md` — read each that exists. Local overlays supersede the pre-loaded standards.

7. **Locate ADRs/PDRs in scope.** For each file in the frozen scope, walk up the directory tree to the repo root collecting `*.adr.md` and `*.pdr.md`. The union is the **applicable decision set**. If none exist, Phase 5 is N/A.

Do not read source files for comprehension during Phase 0. Phase 0 only inventories.

</phase>

<phase number="1" name="automated_gates">

**Goal:** Confirm the project's own quality bar holds before spending comprehension on the code.

Run the canonical validation command from Phase 0. Capture exit code and output.

| Exit code | Verdict for concern 1                                  | Next phase  |
| --------- | ------------------------------------------------------ | ----------- |
| 0         | PASS                                                   | Phase 2     |
| non-zero  | REJECT — record the lint/type errors as the finding    | Phase 6     |

**Do not** manually re-check what linters already cover: type annotations, unused imports, magic numbers, deep relative imports flagged by configured rules, naming conventions. Those concerns are settled by Phase 1.

**Do** flag during Phase 3 anything that requires comprehension to detect: `any` whose suppression comment lacks a real justification (per `<false_positive_handling>`), `@ts-expect-error` whose explanation is "fix later", deep relative imports the linter does not catch.

If the project has no validation command, that is itself a REJECT for concern 1 with the finding "no canonical validation command found in CLAUDE.md, AGENTS.md, package.json, or justfile". Do not invent one.

</phase>

<phase number="2" name="test_execution">

**Goal:** Confirm the test suite passes before evaluating test evidence.

Run the canonical test command. Provision required infrastructure (Docker, DB) when the command fails for missing infrastructure rather than logic — try once. Do not skip tests because infrastructure is unavailable; record that as a REJECT.

| Result                        | Verdict for concern 2                  | Next phase  |
| ----------------------------- | -------------------------------------- | ----------- |
| All tests pass                | PASS                                   | Phase 3     |
| Any failure                   | REJECT — list failing tests as finding | Phase 6     |
| Cannot execute (e.g. missing) | REJECT — record the obstacle           | Phase 6     |

This phase verifies that tests **pass**, not that they have **evidentiary value**. Evidence quality is Phase 4.

</phase>

<phase number="3" name="implementation_comprehension">

**Goal:** Find design flaws by understanding every function in the frozen scope.

Read every file in scope. For every function and method:

1. Read name, parameters, and return type only.
2. Predict what it does in one sentence.
3. Read the body and validate the prediction.
4. If the body matches the prediction, move on.
5. If the body surprises Claude, classify the surprise:

| Surprise                                | Classification                                    | Finding category |
| --------------------------------------- | ------------------------------------------------- | ---------------- |
| Does more than the name says            | SRP violation or misleading name                  | comprehension    |
| Does less than the name says            | Incomplete logic or overpromising name            | comprehension    |
| Parameter unused in body                | Dead parameter (if no interface requires it)      | comprehension    |
| IO mixed with computation               | Tangled design — extract pure core                | design           |
| External dependency imported, not injected | DI violation                                   | design           |
| Variable assigned but never read        | Dead code or abandoned logic                      | comprehension    |
| Branch unreachable given callers        | Dead branch                                       | comprehension    |
| Return value contradicts the type       | Logic bug or wrong return type                    | comprehension    |
| Error throw without context             | Error-quality violation                           | design           |
| Self-referential oracle in test         | Falsifiability violation (handled in Phase 4)     | (defer)          |

Before flagging a dead parameter, check whether the function implements an interface, abstract method, or generic protocol whose contract requires it. If yes, the parameter is contractually required — not a finding.

When evaluating suppression comments — `// eslint-disable-...`, `@ts-expect-error`, `// @ts-ignore` — apply `<false_positive_handling>`. The comment's justification must explain why the rule is wrong in this specific context, not why the author preferred to suppress it.

**Design evaluation across the scope** (one finding per violation, not per file):

- IO and logic separated such that core logic is testable without IO.
- External dependencies injected through parameters, not imported.
- Each function has one responsibility.
- Errors include what failed and the input that triggered it.
- Domain errors use named subclasses, not bare `Error`.

**Import structure** — apply the depth rules from the pre-loaded standard. Same-directory imports OK. One level relative is reviewable. Two or more levels relative is a REJECT unless the import resolves through `scripts/` (boundary code) or a tsconfig path alias.

Findings in this phase always include `file:line`. Findings without a precise location are not findings.

</phase>

<phase number="4" name="test_evidence">

**Goal:** Confirm that tests covering the frozen scope provide genuine evidence.

For every test file that imports any module in the frozen scope, evaluate the test against the assertion-by-assertion gate from `auditing-typescript-tests`. Tests that do not import in-scope modules are out of scope for this run.

For every assertion in the test:

1. **Coupling.** Classify the import relationship to the module under test using the 5-category taxonomy: Direct, Indirect (harness), Transitive, False, Partial. False or Partial coupling is REJECT. Open every imported harness file and trace one level deep — a `vi.mock` inside the harness severs coupling invisibly from the test file.

2. **Falsifiability.** Name a concrete mutation to the module under test that would cause this test to fail. If no such mutation exists, the test is unfalsifiable — REJECT. Sole assertion of `toBeDefined`, `toBeTruthy`, `not.toBeNull`, or `expect.any(...)` is REJECT. Snapshots auto-updated in CI sever falsifiability.

3. **Oracle independence.** Identify the source of each `expect`'s expected value. If the expected value derives from the module under test (`expect(encode(decode(x))).toBe(x)` where both live in the audited module), REJECT. Expected values must come from a canonical constant in another module, an external standard, or a value hand-computed in the test.

4. **Alignment.** Decompose the spec assertion or test name into testable clauses. Every clause must be exercised by at least one `expect`. Single `expect` for a multi-clause assertion is REJECT. The evidence method must match the claim — Property assertions need `fc.assert(fc.property(...))` with a non-trivial arbitrary; `fc.constant` reduces a property to an example.

5. **Mocks.** Every `vi.mock`, `vi.spyOn(...).mockReturnValue(...)`, `jest.mock`, or equivalent must map to a `/testing` Stage 5 exception. Mocks that do not map to an exception are REJECT.

The TypeScript-specific rule from the pre-loaded standard: type-only imports do not count for coupling; `import type` is erased at runtime.

This phase reports a verdict for **concern 4** even when no in-scope tests exist — in that case, REJECT with the finding "no test exercises the in-scope modules" unless the scope is itself test-only.

</phase>

<phase number="5" name="adr_pdr_compliance">

**Goal:** Verify each MUST/NEVER rule in the applicable decision set is honored by the in-scope code.

If the applicable decision set from Phase 0 is empty, concern 5 is N/A.

For every ADR/PDR in the applicable set:

1. Extract every MUST and NEVER rule from the Compliance section.
2. For each rule, search the in-scope code for the pattern that would violate it.
3. A violation is REJECT and cites the ADR/PDR by file path.

Rules to apply directly from the pre-loaded architecture standard:

| ADR Compliance rule                  | Code violation                                        |
| ------------------------------------ | ----------------------------------------------------- |
| "MUST accept runner as parameter"    | Direct `import { execa }` and call without DI         |
| "MUST validate config at load time"  | Untyped config consumed without `.parse()` boundary   |
| "NEVER use vi.mock()"                | `vi.mock(...)` in a test importing the in-scope code  |
| "NEVER shell out without DI wrapper" | Bare `exec`, `execSync`, `spawn` in production module |

If the ADR text itself contradicts the canonical template (temporal voice, missing Compliance section, "Testing Strategy" section present), record a single concern-5 finding "ADR conformance" pointing at the ADR. Do not let a malformed ADR make the audit silently approve.

</phase>

<phase number="6" name="verdict">

**Goal:** Emit the canonical verdict.

1. Construct the verdict using `<output_format>` exactly. Do not add sections. Do not add prose narrative.

2. The decision is APPROVED if and only if every concern row is PASS or N/A. Any REJECT is REJECTED.

3. Print the verdict to the conversation and stop. The skill does not write any file.

The calling workflow is responsible for re-run determinism. To enable re-runs that only verify resolution of prior findings, the caller writes the emitted verdict to `.spx/audits/typescript/<scope-hash>.md` (gitignored operational state). The skill's Phase 0 reads that file when present. Callers that do not need re-run determinism can ignore persistence; every run is then a fresh run.

</phase>

</process>

<re_run_protocol>

When Phase 0 finds a prior verdict at `.spx/audits/typescript/<scope-hash>.md`, this is a re-run. The scope hash matches because the file list and content are identical — meaning either nothing changed since the prior run, or the caller is asking Claude to revisit the same scope after edits that did not modify the listed files.

If the prior verdict was APPROVED and the scope hash matches, return the same APPROVED verdict without re-running phases 1–5. The audit is stable by definition.

If the prior verdict was REJECTED, run the full audit. For every prior finding:

- If the issue is now absent from the code, mark the finding as RESOLVED in the new verdict's "Resolved from prior run" section (only present on re-runs).
- If the issue persists, the new finding cites the same `file:line` and the same root cause — do not rephrase or reframe.

The re-run **never** introduces a finding that:

- Has the same root cause as a prior finding but a different surface phrasing.
- Targets a function or file that was unchanged since the prior verdict and was not flagged before.

When the scope hash differs (the caller scoped a larger or different set of files), this is a new run, not a re-run. Run the full audit and emit a fresh verdict. The caller writes that verdict under the new hash; prior verdicts at other hashes are unaffected.

</re_run_protocol>

<false_positive_handling>

Not every linter or security violation is real. Context matters. Apply this filter during Phase 3 before producing a finding from a suppressed rule.

A suppression is a **false positive** (no finding) when ALL apply:

- The suppression comment names a specific reason tied to the call site, not "fix later" or "we always do this".
- The application context makes the rule's threat model inapplicable (CLI tool with user-trusted input vs. web service with untrusted input).
- An auditor reading the comment can independently verify the safety claim from the surrounding code.

A suppression is a **finding** when ANY apply:

- The justification is missing, vague, or self-referential.
- The threat model still applies (web service, library consumed externally, multi-tenant context).
- The "safety" relies on undocumented invariants elsewhere in the codebase.

Never produce a finding that says "remove the suppression" without verifying that the underlying rule actually applies. Never approve a suppression whose justification Claude cannot articulate in one sentence from the comment text alone.

</false_positive_handling>

<output_format>

Two modes — APPROVED and REJECTED — and nothing else.

<approved_format>

````markdown
# TypeScript Audit — APPROVED

**Scope hash:** `<12-char hash>`
**Files audited:** N
**Run:** fresh | re-run

| # | Concern                          | Status     |
| - | -------------------------------- | ---------- |
| 1 | Automated gates                  | PASS       |
| 2 | Test execution                   | PASS       |
| 3 | Implementation comprehension     | PASS       |
| 4 | Test evidence                    | PASS \| N/A|
| 5 | ADR/PDR compliance               | PASS \| N/A|
| 6 | Determinism contract             | PASS       |
````

That is the complete APPROVED output. No "great work", no "strong architecture", no recommendations, no suggestions for next time. The verdict is the output.

</approved_format>

<rejected_format>

````markdown
# TypeScript Audit — REJECTED

**Scope hash:** `<12-char hash>`
**Files audited:** N
**Run:** fresh | re-run

## Verdict

| # | Concern                          | Status              | One-line detail                                  |
| - | -------------------------------- | ------------------- | ------------------------------------------------ |
| 1 | Automated gates                  | PASS \| REJECT      | <command> exit <code>                            |
| 2 | Test execution                   | PASS \| REJECT \| - | <n> failed of <m>, or "blocked by phase 1"       |
| 3 | Implementation comprehension     | PASS \| REJECT \| - | <n> findings                                     |
| 4 | Test evidence                    | PASS \| REJECT \| N/A | <n> findings                                   |
| 5 | ADR/PDR compliance               | PASS \| REJECT \| N/A | <n> findings against <adr count> decisions    |
| 6 | Determinism contract             | PASS                | always pass when the audit completed             |

## Findings

| # | File:line          | Concern         | Root cause                          | Required fix                                                       |
| - | ------------------ | --------------- | ----------------------------------- | ------------------------------------------------------------------ |
| 1 | src/orders.ts:42   | comprehension   | processOrders tangles IO with logic | Extract pure computeOrderTotals; inject sendEmail via deps         |
| 2 | src/orders.ts:3    | adr-compliance  | Direct sendgrid import — ADR 15-email mandates DI | Replace with EmailSender interface injected through deps |
| 3 | tests/orders.test.ts:18 | test-evidence | Oracle derived from module under test (encode∘decode) | Replace with canonical fixture imported from @testing/fixtures   |

## Detailed Findings

### Finding 1 — processOrders tangles IO with logic

**File:** `src/orders.ts:42`
**Concern:** implementation comprehension, design coherence
**Why this fails:** Predict/verify revealed `processOrders` both computes order totals and calls `sendgrid.send()` for each order. The function cannot be tested without a mail server because IO and computation share a body.

**Correct approach:**

```typescript
function computeOrderTotals(orders: Order[]): OrderSummary[] {
  // pure computation — no IO
}

async function processOrders(
  orders: Order[],
  deps: { sendEmail: EmailSender },
): Promise<void> {
  const summaries = computeOrderTotals(orders);
  for (const summary of summaries) {
    await deps.sendEmail(summary.confirmation);
  }
}
```

(Repeat one detailed-finding block per row in the Findings table. Always cite `file:line`. Always show the corrected snippet.)

## Resolved from prior run (re-runs only)

| # | File:line        | Prior root cause                          | Status   |
| - | ---------------- | ----------------------------------------- | -------- |
| 1 | src/orders.ts:42 | processOrders tangles IO with logic       | RESOLVED |

(Omit this section on a fresh run.)
````

</rejected_format>

**Banned in any verdict:**

- Phrases like "great work", "looks good", "strong architecture", "nice approach", "consider also", "you might want to".
- Hedged statuses like "PASS with notes", "REJECT but minor", "mostly fine".
- Suggestions for "future improvements" — if it is not a finding, it does not appear in the verdict.
- Style observations that are not violations of the pre-loaded standards.
- ADR rewrites, refactor proposals beyond the per-finding corrected snippet.

</output_format>

<failure_modes>

Concrete failures from past audits. Read them and avoid repeating them.

**Approved code with a tangled IO design.** A `processOrders` function computed totals and sent confirmation emails in one body. Linters and tests passed. Claude approved because the function's name was reasonable and the type signature looked clean. The predict/verify protocol would have caught it: the body did more than the name promised, and the design evaluation would have flagged that core logic was untestable without an email service.

**Rejected a parameter as dead.** A function had a `context` parameter never read in the body. Claude flagged it as dead. The function implemented a `CommandHandler` interface contract whose other implementations consumed `context`. Before flagging dead parameters, search for the function's interface or generic constraint.

**Drifted scope on re-run.** First run produced one REJECTED finding for a tangled IO design. Engineer fixed it. Second run produced four new findings on files that had not changed — Claude reread the code and noticed style preferences this time. The re-run protocol exists to prevent this. When the scope hash is unchanged for an unchanged file, the audit verifies prior findings only.

**Hedged the verdict.** First run produced "REJECTED with one minor note" plus a list of "consider"s. The caller could not decide what to do. The output format is binary and the findings table is the entire actionable surface. Either an issue is a finding or it does not appear.

**Mock hidden in a harness.** A test imported `posthogHarness` from `@testing/harnesses/posthog`. No `vi.mock` in the test file. The harness module body contained `vi.mock("posthog-js", ...)`. Coupling was severed at the harness level — invisible from the test file alone. Phase 4 step 6 of `auditing-typescript-tests` opens every imported harness and traces mock calls one level deep. Claude must do the same.

**Self-referential oracle approved.** A property test called `expect(encode(decode(x))).toBe(x)` with `fc.assert(fc.property(...))`. Both `encode` and `decode` were in the module under audit. A shared bug — both stripped trailing whitespace — passed every example. The roundtrip held against the module's own behavior. Independent oracles come from another module, an external standard, or a hand-computed value.

**`fc.constant` disguised as a property test.** A test wrapped `fc.assert(fc.property(fc.constant(...), pred))` and labeled itself a property. The arbitrary held a single value. The test ran one example. Inspect the arbitrary's domain — `fc.constant`, narrow `fc.oneof`, and `fc.nat(1)` reduce a property to examples.

</failure_modes>

<what_to_avoid>

- Do NOT widen scope mid-audit. The frozen scope from Phase 0 governs every subsequent phase.
- Do NOT re-check linter concerns in Phase 3. Phase 1 owns those.
- Do NOT emit findings for style preferences or "could be cleaner" observations.
- Do NOT approve with caveats. The verdict is binary.
- Do NOT propose refactors beyond the per-finding corrected snippet.
- Do NOT modify, create, or delete any file. Persistence of the verdict is the caller's job.
- Do NOT generate new findings on re-run from unchanged code.

</what_to_avoid>

<examples>

Read `${CLAUDE_SKILL_DIR}/references/example-verdicts.md` for an APPROVED verdict, a REJECTED-on-fresh verdict, and a REJECTED-on-re-run verdict.

</examples>

<success_criteria>

Audit is complete when:

- [ ] Scope frozen at Phase 0 and hashed
- [ ] Prior verdict consulted if the hash matched
- [ ] Phases 1–5 executed in order, with each blocking phase honored
- [ ] Verdict produced in canonical format with no banned phrases
- [ ] No file written, edited, or deleted by the skill itself
- [ ] Decision is APPROVED or REJECTED — never anything else
- [ ] On re-run, no finding originates from unchanged unflagged code

</success_criteria>

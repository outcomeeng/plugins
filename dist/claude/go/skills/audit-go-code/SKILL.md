---
name: audit-go-code
description: >-
  Go implementation-code audit methodology — judges the Go code files in
  scope for design flaws, architecture-decision compliance, concurrency
  soundness, and unsafe/cgo soundness.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash(grep:*), Skill
---

Invoke the `go:go-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `go:go-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A verdict on Go implementation code — `APPROVED`, or `REJECTED` with each finding naming the design flaw, boundary violation, ADR/PDR drift, concurrency defect, or unsafe/cgo soundness issue; the violated rule; and the evidence.
</objective>

<repo_local_overlay>
Standards are pre-loaded above. Check for `spx/local/go.md` at the repository root. Read it if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<constraints>

- NEVER modify files, generate fixes, write replacement code, commit changes, or change project state — this audit produces a verdict only.
- NEVER run deterministic validation, formatting, vet, lint, test, or eval commands — this audit reads and judges; it never runs deterministic verification.
- NEVER evaluate test evidence quality — `/audit-go-tests` is the separate concern that judges it.
- ALWAYS keep findings to artifact, violated rule, evidence, and why the cited code violates the rule.
- NEVER include corrective Go samples, implementation patches, prescribed refactors, or required-change summaries in the verdict.
- `APPROVED` means every concern row passes or is explicitly not applicable. `REJECTED` means at least one concern row fails.

</constraints>

<audit_workflow>

Execute the phases in order.

**Phase 0: Scope and product config**

1. Determine the production files in scope
2. Read `CLAUDE.md` and `README.md` for review constraints and naming conventions that inform comprehension — read for context, never to run a gate
3. Read `go.mod` and the linter configuration when present
4. Identify applicable ADRs and PDRs in the spec hierarchy if the code belongs to a spec-tree node

**Phase 1: Code comprehension**

Read every production file. Do not skim.

**1.1 Per-function protocol**

For each function or method:

1. read the name and signature only
2. predict behavior in one sentence
3. read the body
4. investigate surprises

Use this table to classify surprises:

| Surprise                                     | What it suggests                                                |
| -------------------------------------------- | --------------------------------------------------------------- |
| parameter unused in body                     | dead parameter, interface-driven signature, or unfinished logic |
| function does more than its name promises    | SRP violation or misleading name                                |
| function does less than its name promises    | missing behavior or overclaiming name                           |
| error discarded or returned unwrapped        | weak error boundary; `errors.Is` and `errors.As` stop resolving |
| branch appears impossible from call sites    | dead branch or mismatched abstraction                           |
| `context.Context` accepted but not passed on | cancellation lost at this frame                                 |

**1.2 Design evaluation**

Evaluate the codebase for:

- I/O separated from logic
- real seams for process, network, clock, and storage boundaries
- interfaces defined where they are consumed, small, and accepted as parameters
- sentinel or typed errors wrapped with `%w` where the boundary is exported or domain-facing
- narrow packages with coherent responsibility and no package-level mutable state

**1.3 Package and import evaluation**

Classify import paths like this:

| Pattern                                | Classification                                     |
| -------------------------------------- | -------------------------------------------------- |
| `"context"`, `"encoding/json"`         | stdlib, not reviewed                               |
| `"golang.org/x/sync/errgroup"`         | external module, not reviewed                      |
| `"<module>/internal/domain"`           | cross-package codebase import, review              |
| `"<module>/internal/testinfra/..."`    | test infrastructure — rejection in production code |
| an import cycle broken by an interface | review the dependency direction                    |

Import rules:

- production packages import test infrastructure never
- domain packages import adapters never; adapters import domain
- an `internal/` package reaching outside its module subtree is a rejection-level concern

Use `${CLAUDE_SKILL_DIR}/references/false-positive-handling.md` when a suspicious pattern might still be correct in context.

**1.4 Concurrency soundness**

When the scope contains a `go` statement, a channel, a `sync` primitive, or a `context.Context` parameter, run the soundness pass in `${CLAUDE_SKILL_DIR}/references/concurrency-soundness.md`: enumerate every goroutine and its exit condition, check that cancellation reaches every blocking call, check that no mutex is held across a blocking call, and check that shared state has one owner. A goroutine with no exit condition or a lost cancellation is REJECT. A scope with no concurrency skips this subsection.

**1.5 Unsafe and cgo soundness**

When the scope contains `unsafe.Pointer`, `unsafe.Slice`, `unsafe.String`, `import "C"`, or `//export`, run the soundness pass in `${CLAUDE_SKILL_DIR}/references/unsafe-cgo-soundness.md`: enumerate every site, check each conversion for a `SAFETY:` comment tied to the real invariant and against the pointer-lifetime, aliasing, and layout hazard categories, and check each cgo boundary for Go-type conversion, C memory ownership, and pointer-passing rules. A single soundness violation is REJECT. A scope with no such sites skips this subsection.

**Phase 2: ADR and PDR compliance**

Verify each relevant architectural or product constraint is reflected in the code shape. Undocumented deviations make this concern `FAIL`.

</audit_workflow>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/false-positive-handling.md` -- when a surprise is legitimate in Go context
- `${CLAUDE_SKILL_DIR}/references/concurrency-soundness.md` -- soundness pass for goroutines, channels, mutexes, and context
- `${CLAUDE_SKILL_DIR}/references/unsafe-cgo-soundness.md` -- soundness pass for `unsafe` conversions and cgo boundaries
- `${CLAUDE_SKILL_DIR}/references/example-audit.md` -- complete PASS and FAIL examples

</reference_guides>

<verdict_format>

Emit a structured verdict. The skill's entire output is the verdict payload.

The skill's `overall` is `APPROVED` iff every concern row is `PASS` or `NOT_APPLICABLE`; it is `REJECTED` if any concern is `FAIL`. An unavailable required inspection is `FAIL`, never `NOT_APPLICABLE`. Findings use severity `blocking` or `debt`.

```json
{
  "schema_version": 1,
  "skill": "audit-go-code",
  "target": "<scope-target>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    { "name": "function-comprehension", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "design-coherence", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "import-structure", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "concurrency-soundness", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "unsafe-soundness", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "adr-pdr-compliance", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each `NOT_APPLICABLE` row carries `explanation` naming why the concern does not apply. Each finding carries `file`, `line`, `rule` (the concern name or specific violation), `severity: "blocking | debt"`, `message`, `observed`, and `expected`. The message names the violated rule and consequence only; it contains no corrective Go sample, implementation patch, prescribed refactor, or required-change summary.

</verdict_format>

<failure_modes>

**Failure 1: Approved code on the strength of green mechanical gates.** `gofmt`, `go vet`, the linter, and `go test -race` were green, and Claude treated the audit as complete without reading every function. Why it failed: mechanical gates do not catch functions that mix pure logic with I/O, a lost cancellation, weak seams, or ADR/PDR drift — and this audit does not run them anyway; a race-detector-clean run proves only that the executed schedules raced nowhere, not that every goroutine has an owner. How to avoid: spend the whole audit on Phase 1's predict-and-verify pass over every production function in scope; green gates are not the audit.

**Failure 2: Missed a boundary dependency hidden behind a coherent package.** Claude approved a package whose imports looked organized, while a concrete HTTP client was still constructed directly inside business logic. Why it failed: import coherence is separate from boundary design; a module-internal import path can still point at the wrong dependency direction. How to avoid: during design coherence and ADR/PDR compliance, trace each process, network, clock, storage, and cgo boundary to an injected interface or narrow function seam.

**Failure 3: Skipped soundness because no tests failed.** Claude treated green tests as evidence that goroutine ownership, context propagation, and `unsafe` conversions were sound. Why it failed: tests rarely cover the schedule that leaks a goroutine, the blocking call that ignores its context, the pointer that outlives its referent, or the C memory nobody frees. How to avoid: whenever scope contains a `go` statement, a `sync` primitive, a `context.Context` parameter, `unsafe.Pointer`, or `import "C"`, run the matching soundness reference and reject any missing or restated invariant.

</failure_modes>

<success_criteria>

- `APPROVED` means every applicable concern row is `PASS`, every `NOT_APPLICABLE` row explains why the concern does not apply, and every production function in scope was covered.
- `REJECTED` means each finding names the exact code location, violated Go or repository rule, severity, observable consequence, and observed-versus-expected evidence.
- Boundary and design judgments are falsifiable from the cited import path, call path, error path, or package relationship.
- Concurrency judgments identify the goroutine, its owner, and the exit condition or cancellation path being preserved or violated.
- Unsafe and cgo judgments identify the invariant being preserved or violated, including pointer lifetime, aliasing, layout, and C memory ownership when applicable.
- ADR and PDR judgments cite the product constraint being upheld or violated without embedding spec identifiers in code guidance.
- The verdict can be reproduced by another auditor from the listed commands, files read, concern rows, and finding evidence.

</success_criteria>

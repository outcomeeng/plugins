---
name: audit-rust-code
description: >-
  Rust implementation-code audit methodology — judges the Rust code files in
  scope for design flaws, architecture-decision compliance, and unsafe/FFI
  soundness.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(grep:*), Skill
---

{!% require_skill 'rust:rust-standards' %!}

{!% require_skill 'rust:rust-test-standards' %!}

<objective>
A verdict on Rust implementation code — `APPROVED`, or `REJECTED` with each finding naming the design flaw, boundary violation, ADR/PDR drift, or unsafe/FFI soundness issue; the violated rule; and the evidence.
</objective>

<repo_local_overlay>
Standards are pre-loaded above. Check for `spx/local/rust.md` at the repository root. Read it if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<constraints>

- NEVER modify files, generate fixes, write replacement code, commit changes, or change project state — this audit produces a verdict only.
- NEVER run deterministic validation, formatting, lint, test, or eval commands — this audit reads and judges; it never runs deterministic verification.
- NEVER evaluate test evidence quality — `/audit-rust-tests` is the separate concern that judges it.
- ALWAYS keep findings to artifact, violated rule, evidence, and why the cited code violates the rule.
- NEVER include corrective Rust samples, implementation patches, prescribed refactors, or required-change summaries in the verdict.
- `APPROVED` means every concern row passes or is explicitly not applicable. `REJECTED` means at least one concern row fails.

</constraints>

<audit_workflow>

Execute the phases in order.

**Phase 0: Scope and product config**

1. Determine the production files in scope
2. Read `{{! file('root_guide') !}}` and `README.md` for review constraints and naming conventions that inform comprehension — read for context, never to run a gate
3. Read `Cargo.toml` and `rust-toolchain.toml` when present
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

| Surprise                                  | What it suggests                                            |
| ----------------------------------------- | ----------------------------------------------------------- |
| parameter unused in body                  | dead parameter, trait-driven signature, or unfinished logic |
| function does more than its name promises | SRP violation or misleading name                            |
| function does less than its name promises | missing behavior or overclaiming name                       |
| cloned values with no ownership reason    | unclear data flow or borrow-checker avoidance               |
| branch appears impossible from call sites | dead branch or mismatched abstraction                       |
| error loses source context                | weak error boundary                                         |

**1.2 Design evaluation**

Evaluate the codebase for:

- I/O separated from logic
- real seams for process, network, clock, and storage boundaries
- clear ownership flow instead of clone-heavy design
- typed errors where the boundary is public or domain-facing
- narrow modules with coherent responsibility

**1.3 Module and `use` evaluation**

Classify `use` paths like this:

| Pattern                             | Classification                            |
| ----------------------------------- | ----------------------------------------- |
| `use std::collections::BTreeMap;`   | stdlib, not reviewed                      |
| `use serde::Deserialize;`           | external crate, not reviewed              |
| `use crate::domain::UserId;`        | cross-module codebase import, review      |
| `use super::parser::parse;`         | nearby private module import, review      |
| `use super::super::shared::Config;` | deep relative import, review aggressively |

Import rules:

- prefer `crate::` for stable cross-module references
- use `self::` or `super::` for nearby private modules that move together
- two or more `super::` hops in production code are a rejection-level concern unless the module is a tightly scoped private leaf
- production code must not depend on test-only helpers

Use `${CLAUDE_SKILL_DIR}/references/false-positive-handling.md` when a suspicious pattern might still be correct in context.

**1.4 Unsafe and FFI soundness**

When the scope contains an `unsafe` block, `unsafe fn`, `unsafe impl`, or `extern "C"` / `#[no_mangle]` boundary, run the soundness pass in `${CLAUDE_SKILL_DIR}/references/unsafe-soundness.md`: enumerate every unsafe site, check each block for a `SAFETY:` comment tied to the real invariant and against the pointer, aliasing, lifetime, validity, FFI, and `Send`/`Sync` hazard categories, and check each FFI boundary for ABI-stable types, panic containment, and documented pointer contracts. A single soundness violation is REJECT. A scope with no unsafe sites skips this subsection.

**Phase 2: ADR and PDR compliance**

Verify each relevant architectural or product constraint is reflected in the code shape. Undocumented deviations make this concern `FAIL`.

</audit_workflow>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/false-positive-handling.md` -- when a surprise is legitimate in Rust context
- `${CLAUDE_SKILL_DIR}/references/unsafe-soundness.md` -- soundness pass for `unsafe` blocks and FFI boundaries
- `${CLAUDE_SKILL_DIR}/references/example-audit.md` -- complete PASS and FAIL examples

</reference_guides>

<verdict_format>

Emit a structured verdict. The skill's entire output is the verdict payload.

The skill's `overall` is `APPROVED` iff every concern row is `PASS` or `NOT_APPLICABLE`; it is `REJECTED` if any concern is `FAIL`. An unavailable required inspection is `FAIL`, never `NOT_APPLICABLE`. Findings use severity `blocking` or `debt`.

```json
{
  "schema_version": 1,
  "skill": "audit-rust-code",
  "target": "<scope-target>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    { "name": "function-comprehension", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "design-coherence", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "import-structure", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "unsafe-soundness", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "adr-pdr-compliance", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each `NOT_APPLICABLE` row carries `explanation` naming why the concern does not apply. Each finding carries `file`, `line`, `rule` (the concern name or specific violation), `severity: "blocking | debt"`, `message`, `observed`, and `expected`. The message names the violated rule and consequence only; it contains no corrective Rust sample, implementation patch, prescribed refactor, or required-change summary.

</verdict_format>

<failure_modes>

**Failure 1: Approved code on the strength of green mechanical gates.** `cargo fmt`, `cargo clippy`, and `cargo test` were green, and Claude treated the audit as complete without reading every function. Why it failed: mechanical gates do not catch functions that mix pure logic with I/O, unclear ownership flow, weak seams, or ADR/PDR drift — and this audit does not run them anyway. How to avoid: spend the whole audit on Phase 1's predict-and-verify pass over every production function in scope; green gates are not the audit.

**Failure 2: Missed a boundary dependency hidden behind a coherent module.** Claude approved a module whose imports looked organized, while a concrete external client was still imported directly inside business logic. Why it failed: import coherence is separate from boundary design; `crate::` paths can still point at the wrong dependency direction. How to avoid: during design coherence and ADR/PDR compliance, trace each process, network, clock, storage, and FFI boundary to an injected trait or narrow function seam.

**Failure 3: Skipped unsafe soundness because no tests failed.** Claude treated green tests as evidence that `unsafe` and FFI boundaries were sound. Why it failed: tests rarely cover pointer validity, aliasing, lifetime, unwind, ABI, or `Send`/`Sync` invariants. How to avoid: whenever scope contains `unsafe`, `unsafe fn`, `unsafe impl`, `extern "C"`, or `#[no_mangle]`, run `${CLAUDE_SKILL_DIR}/references/unsafe-soundness.md` and reject any missing or mismatched invariant.

</failure_modes>

<success_criteria>

- `APPROVED` means every applicable concern row is `PASS`, every `NOT_APPLICABLE` row explains why the concern does not apply, and every production function in scope was covered.
- `REJECTED` means each finding names the exact code location, violated Rust or repository rule, severity, observable consequence, and observed-versus-expected evidence.
- Boundary and design judgments are falsifiable from the cited import path, call path, ownership flow, error path, or module relationship.
- Unsafe and FFI judgments identify the invariant being preserved or violated, including pointer validity, aliasing, lifetime, ABI, unwind, and thread-safety constraints when applicable.
- ADR and PDR judgments cite the product constraint being upheld or violated without embedding spec identifiers in code guidance.
- The verdict can be reproduced by another auditor from the listed commands, files read, concern rows, and finding evidence.

</success_criteria>

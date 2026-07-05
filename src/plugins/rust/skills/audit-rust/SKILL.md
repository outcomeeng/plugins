---
name: audit-rust
description: >-
  Rust implementation-code audit methodology — design flaws, ADR compliance, and unsafe/FFI soundness — composed by a generic auditor agent for the Rust files in scope.
  Reached only through a dispatched auditor agent, never the main conversation.
allowed-tools: Read, Bash, Glob, Grep, Skill
---

{!% require_skill 'rust:rust-standards' %!}

{!% require_skill 'rust:rust-test-standards' %!}

<dispatch_gate>

This audit runs inside a dispatched auditor's verifier context — a generic auditor agent (`auditor` or `audit-orchestrator`) composing this skill for the Rust files in scope — isolated from the author context that produced the work under audit. When this skill loads in the author/main conversation rather than inside a dispatched auditor agent, STOP — the audit must run in that verifier context. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>
A verdict on Rust implementation code — APPROVED, or REJECTED with each finding naming the design flaw, boundary violation, ADR/PDR drift, or unsafe/FFI soundness issue; the violated rule; and the evidence.
</objective>

<repo_local_overlay>
Standards are pre-loaded above. Check for `spx/local/rust.md` at the repository root. Read it if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<constraints>

Comprehension is the whole job. This skill runs no deterministic verification of its own — no formatter, linter, or test run. The caller brings the project's formatting, linting, and tests to passing on the changeset before dispatching this audit, and CI re-runs them over the whole repository. Read names and signatures first, predict behavior, then read the body and look for surprises. Review time belongs to design and semantics, not restating what `clippy` already checked or re-running what the caller already passed.

This skill audits implementation code. Test evidence quality belongs to `/audit-rust-tests`. If test files are in scope, load `/rust-test-standards` and hand off evidence judgments to the test auditor — do not run the test suite; the caller already passed it before dispatch.

The verdict is binary. APPROVED means every concern passes. REJECTED means at least one concern fails.

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

Verify each relevant architectural or product constraint is reflected in the code shape. Undocumented deviations are REJECTED.

</audit_workflow>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/false-positive-handling.md` -- when a surprise is legitimate in Rust context
- `${CLAUDE_SKILL_DIR}/references/unsafe-soundness.md` -- soundness pass for `unsafe` blocks and FFI boundaries
- `${CLAUDE_SKILL_DIR}/references/example-audit.md` -- complete APPROVED and REJECTED examples

</reference_guides>

<verdict_format>

Emit the verdict as JSON conforming to the canonical audit-verdict schema consumed by the composing audit workflow. The skill's entire output is the JSON verdict. The composing audit workflow records and renders the verdict through the audit journal path.

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "audit-rust",
  "target": "<scope-target>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "function-comprehension", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "design-coherence", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "import-structure", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "unsafe-soundness", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "adr-pdr-compliance", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding carries `file`, `line`, `rule` (the concern name or specific violation), `severity: "REJECT"`, and `message` (the one-line "why this fails"). Include correct-approach Rust samples and required-changes summary directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</verdict_format>

<failure_modes>

**Failure 1: Approved code on the strength of green mechanical gates.** The caller's `cargo fmt`, `cargo clippy`, and `cargo test` passed before dispatch, and Claude treated the audit as complete without reading every function. Why it failed: mechanical gates do not catch functions that mix pure logic with I/O, unclear ownership flow, weak seams, or ADR/PDR drift — and this audit does not re-run them anyway. How to avoid: spend the whole audit on Phase 1's predict-and-verify pass over every production function in scope; the green gates are a precondition, not the audit.

**Failure 2: Missed a boundary dependency hidden behind a coherent module.** Claude approved a module whose imports looked organized, while a concrete external client was still imported directly inside business logic. Why it failed: import coherence is separate from boundary design; `crate::` paths can still point at the wrong dependency direction. How to avoid: during design coherence and ADR/PDR compliance, trace each process, network, clock, storage, and FFI boundary to an injected trait or narrow function seam.

**Failure 3: Skipped unsafe soundness because no tests failed.** Claude treated green tests as evidence that `unsafe` and FFI boundaries were sound. Why it failed: tests rarely cover pointer validity, aliasing, lifetime, unwind, ABI, or `Send`/`Sync` invariants. How to avoid: whenever scope contains `unsafe`, `unsafe fn`, `unsafe impl`, `extern "C"`, or `#[no_mangle]`, run `${CLAUDE_SKILL_DIR}/references/unsafe-soundness.md` and reject any missing or mismatched invariant.

</failure_modes>

<success_criteria>

- APPROVED means every applicable concern row is PASS, every non-applicable UNKNOWN row explains why the concern does not apply, and every production function in scope was covered.
- REJECTED means each finding names the exact code location, violated Rust or repository rule, observable consequence, and required correction.
- Boundary and design judgments are falsifiable from the cited import path, call path, ownership flow, error path, or module relationship.
- Unsafe and FFI judgments identify the invariant being preserved or violated, including pointer validity, aliasing, lifetime, ABI, unwind, and thread-safety constraints when applicable.
- ADR and PDR judgments cite the product constraint being upheld or violated without embedding spec identifiers in code guidance.
- The verdict can be reproduced by another auditor from the listed commands, files read, concern rows, and finding evidence.

</success_criteria>

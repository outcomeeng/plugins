---
name: auditing-rust
description: Use when asked by the user to invoke the Rust code audit skill
---

Invoke the `rust:standardizing-rust` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `rust:standardizing-rust-tests` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Review Rust implementation code after the mechanical checks pass. Find design flaws, boundary violations, and ADR or PDR drift that automated gates do not catch. This skill is read-only.
</objective>

<quick_start>

1. Standards are pre-loaded above. Also check for `spx/local/rust.md` if it exists.
2. If test files are part of the review scope, read `/standardizing-rust-tests` and `/testing-rust` for test-shape context, then hand off evidence judgments to `/auditing-rust-tests`.
3. Read `CLAUDE.md`, `Cargo.toml`, and `rust-toolchain.toml` when present.
4. Run the repository's declared validation command. If none is declared, use the fallback full sequence: `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings`, `cargo test --all-targets`.
5. Read every production file in scope with the predict and verify protocol.
6. Check the final code shape against applicable ADR and PDR constraints.

</quick_start>

<repo_local_overlays>
Standards are pre-loaded above. Check for `spx/local/rust.md` at the repository root. Read it if it exists and enforce it as the repo-local specialization.
</repo_local_overlays>

<essential_principles>

Automated gates are the entry ticket. If formatting, linting, or tests fail, reject immediately and stop. Manual review starts only after the code passes the mechanical bar.

Comprehension is the main job. Read names and signatures first, predict behavior, then read the body and look for surprises. Review time belongs to design and semantics, not restating what `clippy` already checked.

This skill audits implementation code. Test evidence quality belongs to `/auditing-rust-tests`. If test files are in scope, load `/standardizing-rust-tests`, verify they pass, then hand off evidence judgments to the test auditor.

The verdict is binary. APPROVED means every concern passes. REJECTED means at least one concern fails.

</essential_principles>

<process>

Execute the phases in order.

**Phase 0: Scope and product config**

1. Determine the production files in scope
2. Read `CLAUDE.md` and `README.md` for product commands and review constraints
3. Read `Cargo.toml` and `rust-toolchain.toml` when present
4. Identify applicable ADRs and PDRs in the spec hierarchy if the code belongs to a spec-tree node

**Phase 1: Automated gates** (blocking)

Run the repository's canonical validation command. If the repository does not publish one, use the fallback sequence from `rules/validation-sequence.json`.

Non-zero exit means REJECTED. Do not proceed to manual review.

**Phase 2: Test execution** (blocking)

Run the full test suite. If the repo has a stricter documented command, use it. Otherwise `cargo test --all-targets` is the minimum bar.

Any failing test means REJECTED. Do not proceed.

**Phase 3: Code comprehension**

Read every production file. Do not skim.

**3.1 Per-function protocol**

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

**3.2 Design evaluation**

Evaluate the codebase for:

- I/O separated from logic
- real seams for process, network, clock, and storage boundaries
- clear ownership flow instead of clone-heavy design
- typed errors where the boundary is public or domain-facing
- narrow modules with coherent responsibility

**3.3 Module and `use` evaluation**

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

Use `references/false-positive-handling.md` when a suspicious pattern might still be correct in context.

**Phase 4: ADR and PDR compliance**

Verify each relevant architectural or product constraint is reflected in the code shape. Undocumented deviations are REJECTED.

</process>

<reference_guides>

- `references/false-positive-handling.md` -- when a surprise is legitimate in Rust context
- `references/example-audit.md` -- complete APPROVED and REJECTED examples
- `rules/validation-sequence.json` -- fallback validation sequence metadata
- `rules/review-prompts.js` -- fallback manual review prompts
- `rules/security-signals.yaml` -- fallback security review signals

</reference_guides>

<output_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/auditing/scripts/verdict.py`. The skill's entire output is the JSON verdict. The calling agent or orchestrator captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff every concern row is `PASS` or `UNKNOWN` (N/A maps to `UNKNOWN`); `FAIL` if any concern is `FAIL`. Findings carry severity `REJECT` for blocking violations.

```json
{
  "schema_version": 1,
  "skill": "auditing-rust",
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

Each finding carries `file`, `line`, `rule` (the concern name or specific violation), `severity: "REJECT"`, and `message` (the one-line "why this fails"). Include correct-approach Rust samples and required-changes summary directly in the finding's `message` field — the JSON verdict is the complete output of this skill.

</output_format>

<success_criteria>

- repo-local Rust overlays were loaded when present
- automated gates passed before manual review started
- full tests passed before manual review started
- every production function in scope was read with the predict and verify protocol
- design review covered seams, ownership flow, error quality, and module cohesion
- ADR and PDR constraints were checked when applicable
- verdict is structured and binary

</success_criteria>

---
name: auditing-rust
description: ALWAYS invoke this skill when auditing code for Rust or after writing code. NEVER modify a spec to match code without auditing the code first.
allowed-tools: Read, Bash, Glob, Grep
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust/SKILL.md" || echo "standardizing-rust not found — invoke rust:standardizing-rust manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust-tests/SKILL.md" || echo "standardizing-rust-tests not found — invoke rust:standardizing-rust-tests manually"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. `rust:standardizing-rust`
2. `rust:standardizing-rust-tests`

</codex_fallback>

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

**Phase 0: Scope and project config**

1. Determine the production files in scope
2. Read `CLAUDE.md` and `README.md` for project commands and review constraints
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
- `references/example-review.md` -- complete APPROVED and REJECTED examples
- `rules/validation-sequence.json` -- fallback validation sequence metadata
- `rules/review-prompts.js` -- fallback manual review prompts
- `rules/security-signals.yaml` -- fallback security review signals

</reference_guides>

<output_format>

````text
CODE REVIEW

Decision: [APPROVED | REJECTED]

Verdict

| # | Concern                | Status            | Detail            |
| - | ---------------------- | ----------------- | ----------------- |
| 1 | Automated gates        | {PASS/REJECT}     | {one-line detail} |
| 2 | Test execution         | {PASS/REJECT}     | {one-line detail} |
| 3 | Function comprehension | {PASS/REJECT}     | {one-line detail} |
| 4 | Design coherence       | {PASS/REJECT}     | {one-line detail} |
| 5 | Import structure       | {PASS/REJECT/N/A} | {one-line detail} |
| 6 | ADR/PDR compliance     | {PASS/REJECT/N/A} | {one-line detail} |

---

Findings (REJECTED only)

Finding: {Finding name}

Where: {file:line or section}
Concern: {which concern from verdict table}
Why this fails: {direct explanation}

Correct approach:

```rust
{What the code should look like}
```

---

Required Changes (REJECTED only)

{concise list}

---

{If REJECTED: "Fix issues and resubmit for review."}
{If APPROVED: "Code meets standards."}
````

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

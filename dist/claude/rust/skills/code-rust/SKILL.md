---
name: code-rust
description: ALWAYS invoke this skill when writing or fixing implementation code for Rust. NEVER write or repair Rust implementation code without this skill.
allowed-tools: Read, Write, Glob, Grep, Edit, Skill, Bash(cargo fmt --check:*), Bash(cargo clippy:*), Bash(cargo test:*)
---

Invoke the `rust:rust-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `rust:rust-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Rust implementation code with spec-driven behavior, explicit seams, and full validation passing.
</objective>

<accessing_skill_files>
When this skill is invoked, Claude Code provides the base directory in the loading message:

```text
Base directory for this skill: ${CLAUDE_SKILL_DIR}
```

Use this path to access skill files:

- References: `${CLAUDE_SKILL_DIR}/references/`
- Workflows: `${CLAUDE_SKILL_DIR}/workflows/`

Do not search the product directory for skill files when the loading message already provides the base path.
</accessing_skill_files>

<quick_start>

1. Read the repo-local Rust overlays when present; the standards above are already loaded.
2. If this is a spec-tree work item, invoke `spec-tree:contextualize` before editing code.
3. Read `${CLAUDE_SKILL_DIR}/workflows/implementation.md` for new work or `${CLAUDE_SKILL_DIR}/workflows/remediation.md` for review feedback.
4. Invoke `/verify` when behavior changes require new or revised evidence; use `/test-rust` for Rust expression after test is selected.
5. Finish with the repository validation sequence or, if none is published, `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings`, and `cargo test --all-targets`.

`allowed-tools` preapproves only the listed raw-tool fallbacks. A repository-canonical wrapper outside those patterns uses the runtime's normal per-call approval path; NEVER select a fallback merely to avoid that approval.

</quick_start>

<essential_principles>

Behavior comes from specs and their selected test, eval, or audit evidence. Existing code is reference material, not authority.

Prefer explicit ownership, typed errors, and narrow seams over framework-heavy indirection. Traits and function parameters are for real architectural boundaries, not for decoration.

No generated mocks as the default testing strategy. When a controlled implementation is needed, keep coupling to the real seam with a small hand-written recorder, harness, or trait implementation.

Do not declare work complete until the full validation sequence passes.

</essential_principles>

<repo_local_overlay>
After loading `/rust-standards` and `/rust-test-standards`, check for `spx/local/rust.md` and `spx/local/rust-tests.md` at the repository root. Read each file that exists before discovery and implementation. Treat each as repo-local routing to the product's governing specs and decisions; a local overlay supplements skill behavior and does not declare product truth.
</repo_local_overlay>

<hierarchy_of_authority>
Use guidance in this order:

1. this skill and its loaded Rust standards
2. loaded ADRs, PDRs, and spec-tree artifacts
3. `CLAUDE.md`, `README.md`, `docs/`, and other product documentation
4. selected test, eval, or pathless audit evidence
5. existing code as the lowest-layer reference

When layers disagree, the higher authority wins.
</hierarchy_of_authority>

<codebase_discovery>
Before writing code, discover what already exists.

Read:

- `README.md`, `docs/`, `CLAUDE.md`, and `CONTRIBUTING.md` when present
- `Cargo.toml` for crate layout, features, lints, and dependencies
- `rust-toolchain.toml` when present

Search for:

- similar modules, traits, structs, and error types
- existing seam patterns for process, storage, network, and time boundaries
- logging and tracing conventions
- fixture and harness modules used by nearby tests

Before implementation, confirm:

- which crates are already available
- which module naming and error patterns the repository uses
- whether an existing seam or helper already solves the problem

</codebase_discovery>

<testing_methodology>
Invoke `/verify` before adding or revising evidence. When it selects test, use `/test-rust` for Rust expression and follow RED/GREEN. When it selects evaluate, read the eval definition, cases, materialized prompt, real producer contract, selected product command, and threshold; run that command before and after implementation. When it selects audit, preserve the pathless requirement for the isolated verifier without inventing a test. If the change alters behavior and no evidence already proves that behavior, establish the selected evidence first.

Use `/rust-test-standards` as the canonical source for filenames, evidence levels, controlled implementations, property tests, compile-fail evidence, fixture placement, and coverage expectations. Keep production code aligned with those constraints instead of re-declaring test policy here.
</testing_methodology>

<audit_requirement_handoff>

For each `/verify` routing row whose verification type is audit, re-read the routed spec or decision artifact and confirm the exact subject still carries `([audit])`. The completion report includes one `Audit requirements` row per audit routing row with the full `spx/...` source path, exact subject text, and status `preserved`. The row count must equal the routing result's audit-row count; when that count is zero, report `Audit requirements: none selected`.

</audit_requirement_handoff>

<context_loading>
If this work belongs to a spec-tree node:

1. invoke `spec-tree:contextualize` with the full path
2. abort if required context is missing
3. implement only after the context is loaded

If the work is outside the spec tree, proceed with the provided requirements and repository context.
</context_loading>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/outcome-engineering-patterns.md` -- Rust-native code patterns for seams, config, errors, and cleanup
- `${CLAUDE_SKILL_DIR}/references/test-patterns.md` -- debuggability-first Rust test organization
- `${CLAUDE_SKILL_DIR}/references/verification-checklist.md` -- completion checks and validation commands
- `${CLAUDE_SKILL_DIR}/workflows/implementation.md` -- protocol for new implementation work
- `${CLAUDE_SKILL_DIR}/workflows/remediation.md` -- protocol for fixing review feedback

</reference_guides>

<failure_modes>

**Failure 1: Wrote a test whose body only calls a harness.** Claude produced `#[test]` bodies that were a single `<product>_testing::harnesses::*::assert_*(...)` call, following the shape this skill's own test-patterns reference then carried in all five of its examples. Why it failed: the harness both acted and judged, so a failing case reported a panic from inside infrastructure instead of an actual-against-expected comparison, and inverting the claim meant editing the harness every other test shared. How to avoid: keep the assertion macro in the `#[test]` body. A harness supplies setup, resources, and property-run policy; a generator supplies the domain; the source module owns the case values and expected results. Treat any bare `harness::assert_*` call as the anti-pattern `${CLAUDE_SKILL_DIR}/references/test-patterns.md` `<anti_patterns>` names first.

</failure_modes>

<success_criteria>

- The Rust implementation satisfies its governed evidence with no unresolved implementation-audit finding.
- The repository's canonical format and lint commands pass; its regression test command passes; every test or eval command selected by `/verify` passes its declared criterion.
- Behavior-changing work has selected test or eval evidence, or an `Audit requirements` report whose `preserved` rows match `/verify`'s audit routing rows.
- No temporary debug code, commented-out implementation, or TODO/FIXME escape hatch remains.

</success_criteria>

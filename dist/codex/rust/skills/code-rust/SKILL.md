---
name: code-rust
description: ALWAYS invoke this skill when writing or fixing implementation code for Rust. NEVER write or repair Rust implementation code without this skill.
allowed-tools: Read, Write, Glob, Grep, Edit, Skill
---

Invoke the `rust:rust-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `rust:rust-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Rust implementation code with spec-driven behavior, explicit seams, and full validation passing.
</objective>

<accessing_skill_files>
When this skill is invoked, the runtime provides the skill base directory in the loading message:

```text
Base directory for this skill: ${SKILL_DIR}
```

Use this path to access skill files:

- References: `${SKILL_DIR}/references/`
- Workflows: `${SKILL_DIR}/workflows/`

Do not search the product directory for skill files when the loading message already provides the base path.
</accessing_skill_files>

<reference_loading>
**Standards are pre-loaded above.** After loading, check for `spx/local/rust.md` and `spx/local/rust-tests.md` at the repository root. Read each file that exists and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</reference_loading>

<quick_start>

1. Read `/rust-standards`, `/rust-test-standards`, and repo-local Rust overlays when present.
2. If this is a spec-tree work item, invoke `/contextualize` before editing code.
3. Read `${SKILL_DIR}/workflows/implementation.md` for new work or `${SKILL_DIR}/workflows/remediation.md` for review feedback.
4. Use `/test-rust` when behavior changes require new or revised tests.
5. Finish with the repository validation sequence or, if none is published, `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings`, `cargo check --all-targets --all-features`, and `cargo test --all-targets`.

</quick_start>

<essential_principles>

Behavior comes from specs and tests. Existing code is reference material, not authority.

Prefer explicit ownership, typed errors, and narrow seams over framework-heavy indirection. Traits and function parameters are for real architectural boundaries, not for decoration.

No generated mocks as the default testing strategy. When a controlled implementation is needed, keep coupling to the real seam with a small hand-written recorder, harness, or trait implementation.

Do not declare work complete until the full validation sequence passes.

</essential_principles>

<repo_local_overlay>
After loading `/rust-standards` and `/rust-test-standards`, check for `spx/local/rust.md` and `spx/local/rust-tests.md` at the repository root. Read each file that exists before discovery and implementation. Treat each as repo-local routing to the product's governing specs and decisions; a local overlay supplements skill behavior and does not declare product truth.
</repo_local_overlay>

<hierarchy_of_authority>
Use guidance in this order:

1. `README.md`, `docs/`, and other product documentation
2. `AGENTS.md`
3. ADRs, PDRs, and spec-tree artifacts
4. this skill and its helper files
5. existing code as reference only

When documentation and code disagree, documentation wins.
</hierarchy_of_authority>

<codebase_discovery>
Before writing code, discover what already exists.

Read:

- `README.md`, `docs/`, `AGENTS.md`, and `CONTRIBUTING.md` when present
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
Invoke `/test-rust` before adding or revising tests. If the change alters behavior and no test already proves that behavior, write or extend tests first.

Use `/rust-test-standards` as the canonical source for filenames, evidence levels, controlled implementations, property tests, compile-fail evidence, fixture placement, and coverage expectations. Keep production code aligned with those constraints instead of re-declaring test policy here.
</testing_methodology>

<context_loading>
If this work belongs to a spec-tree node:

1. invoke `/contextualize` with the full path
2. abort if required context is missing
3. implement only after the context is loaded

If the work is outside the spec tree, proceed with the provided requirements and repository context.
</context_loading>

<reference_guides>

- `${SKILL_DIR}/references/outcome-engineering-patterns.md` -- Rust-native code patterns for seams, config, errors, and cleanup
- `${SKILL_DIR}/references/test-patterns.md` -- debuggability-first Rust test organization
- `${SKILL_DIR}/references/verification-checklist.md` -- completion checks and validation commands
- `${SKILL_DIR}/workflows/implementation.md` -- protocol for new implementation work
- `${SKILL_DIR}/workflows/remediation.md` -- protocol for fixing review feedback

</reference_guides>

<failure_modes>

**Claude completed Rust validation without a compile check.** What happened: formatting, clippy, and tests passed, while the workflow claimed a separate compile/type-check result it never ran. Why it failed: the quick start and implementation workflow carried different validation bundles. How to avoid: use the repository's canonical validation sequence, or run the complete fallback sequence including `cargo check --all-targets --all-features`, then report every exact command and exit status.

</failure_modes>

<success_criteria>

- Every implemented behavior satisfies its linked spec assertion and passes the corresponding Rust evidence tests.
- Public APIs, ownership boundaries, typed errors, modules, and injected seams conform to the loaded ADRs and repository contracts.
- Controlled implementations preserve the real production boundary and do not replace the behavior under test with generated mocks.
- Every unsafe block or FFI boundary states and upholds its safety invariant when the implementation contains unsafe code.
- The completion report records the exact formatting, lint, compile, and test commands, each with exit status zero.

</success_criteria>

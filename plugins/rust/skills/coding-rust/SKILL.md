---
name: coding-rust
description: ALWAYS invoke this skill when writing or fixing implementation code for Rust. NEVER write or repair Rust implementation code without this skill.
allowed-tools: Read, Write, Bash, Glob, Grep, Edit
---

<objective>
Write or repair Rust implementation code with spec-driven behavior, repository-aware discovery, explicit seams, and full validation before completion.
</objective>

<accessing_skill_files>
When this skill is invoked, Claude Code provides the base directory in the loading message:

```text
Base directory for this skill: {skill_dir}
```

Use this path to access skill files:

- References: `{skill_dir}/references/`
- Workflows: `{skill_dir}/workflows/`

Do not search the project directory for skill files when the loading message already provides the base path.
</accessing_skill_files>

<reference_loading>
Before discovery or implementation, read `/standardizing-rust`, then `/standardizing-rust-tests`. After that, check for `spx/local/rust.md` and `spx/local/rust-tests.md` at the repository root. Read each file that exists and apply it as the repo-local specialization.
</reference_loading>

<quick_start>

1. Read `/standardizing-rust`, `/standardizing-rust-tests`, and repo-local Rust overlays when present.
2. If this is a spec-tree work item, invoke `spec-tree:contextualizing` before editing code.
3. Read `workflows/implementation.md` for new work or `workflows/remediation.md` for review feedback.
4. Use `/testing-rust` when behavior changes require new or revised tests.
5. Finish with the repository validation sequence or, if none is published, `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings`, and `cargo test --all-targets`.

</quick_start>

<essential_principles>

Behavior comes from specs and tests. Existing code is reference material, not authority.

Prefer explicit ownership, typed errors, and narrow seams over framework-heavy indirection. Traits and function parameters are for real architectural boundaries, not for decoration.

No generated mocks as the default testing strategy. When a controlled implementation is needed, keep coupling to the real seam with a small hand-written recorder, harness, or trait implementation.

Do not declare work complete until the full validation sequence passes.

</essential_principles>

<repo_local_overlays>
After loading `/standardizing-rust` and `/standardizing-rust-tests`, check for `spx/local/rust.md` and `spx/local/rust-tests.md` at the repository root. Read each file that exists before discovery and implementation. Treat them as repo-local specializations of the generic Rust standards.
</repo_local_overlays>

<hierarchy_of_authority>
Use guidance in this order:

1. `README.md`, `docs/`, and other project documentation
2. `CLAUDE.md`
3. ADRs, PDRs, and spec-tree artifacts
4. this skill and its helper files
5. existing code as reference only

When documentation and code disagree, documentation wins.
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
Invoke `/testing-rust` before adding or revising tests. If the change alters behavior and no test already proves that behavior, write or extend tests first.

Use `/standardizing-rust-tests` as the canonical source for filenames, evidence levels, controlled implementations, property tests, compile-fail evidence, fixture placement, and coverage expectations. Keep production code aligned with those constraints instead of re-declaring test policy here.
</testing_methodology>

<context_loading>
If this work belongs to a spec-tree node:

1. invoke `spec-tree:contextualizing` with the full path
2. abort if required context is missing
3. implement only after the context is loaded

If the work is outside the spec tree, proceed with the provided requirements and repository context.
</context_loading>

<reference_guides>

- `references/outcome-engineering-patterns.md` -- Rust-native code patterns for seams, config, errors, and cleanup
- `references/test-patterns.md` -- debuggability-first Rust test organization
- `references/verification-checklist.md` -- completion checks and validation commands
- `workflows/implementation.md` -- protocol for new implementation work
- `workflows/remediation.md` -- protocol for fixing review feedback

</reference_guides>

<success_criteria>

- repo-local Rust overlays were loaded when present
- `/standardizing-rust-tests` was loaded before behavior-changing implementation work
- codebase discovery happened before implementation
- behavior-changing work is backed by tests or an explicit review constraint
- new code follows repository patterns for seams, ownership, errors, and modules
- full validation passed before completion

</success_criteria>

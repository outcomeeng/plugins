---
name: architecting-rust
description: ALWAYS invoke this skill when writing ADRs for Rust.
allowed-tools: Read, Write, Glob, Grep
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust/SKILL.md" || echo "standardizing-rust not found — invoke rust:standardizing-rust manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-rust-architecture/SKILL.md" || echo "standardizing-rust-architecture not found — invoke rust:standardizing-rust-architecture manually"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. `rust:standardizing-rust`
2. `rust:standardizing-rust-architecture`

</codex_fallback>

<objective>
Create Rust ADRs that follow the standard Rust architecture template, preserve spec-tree hierarchy constraints, and encode testability as Compliance rules.
</objective>

<essential_principles>
**Standards are pre-loaded above.** The first skill defines shared Rust standards; the architecture standard defines canonical ADR sections, how testability appears in Compliance rules, and what does not belong in an ADR.

After reading those standards, check for `spx/local/rust.md` and `spx/local/rust-architecture.md` at the repository root. Read each file that exists and apply it as the repo-local specialization.

- ADRs follow the authoritative template: Purpose, Context, Decision, Rationale, Trade-offs, Invariants, Compliance
- Testability constraints go in the Compliance section as MUST/NEVER rules -- not in a separate Testing Strategy section
- Prefer type-level invariants over runtime-only validation when the domain allows it
- Design around ownership, borrowing, and resource lifetimes explicitly
- Design for dependency injection (NO MOCKING)
- You produce ADRs (Architecture Decision Records), not implementation code

</essential_principles>

<context_loading>
**For spec-tree work items: Load complete context before creating ADRs.**

If you're creating ADRs for a spec-tree work item (enabler/outcome), ensure complete hierarchical context is loaded:

1. **Invoke `spec-tree:contextualizing`** with the node path
2. **Verify all ancestor ADRs/PDRs are loaded** - Must understand and honor all decision records in hierarchy
3. **Read the node spec** - Requirements, Test Strategy, and Outcomes sections

**The `spec-tree:contextualizing` skill provides:**

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Node spec with requirements, test strategy, and outcomes
- Typed assertions from the target node

**ADR creation requirements:**

- Must not contradict ancestor ADRs/PDRs (product → ancestor hierarchy)
- Must reference relevant ancestor decisions
- Must include testability constraints in Compliance (MUST/NEVER rules for DI, no mocking)
- Must document trade-offs and consequences

**If NOT working on spec-tree work item**: Proceed directly with ADR creation using provided requirements.
</context_loading>

<input_context>
Before creating ADRs, you must understand:

**1. Node Specification**

- Functional requirements in `## Requirements` section
- Test strategy in `## Test Strategy` section
- Typed assertions from the node spec
- Architectural constraints from ancestor ADRs

**2. Project Context**

Read these files to understand project structure and workflow:

- `spx/CLAUDE.md` - Project navigation, work item status, BSP dependencies

For Rust test standards and methodology, read `/standardizing-rust-tests`, then invoke `/testing-rust`.

**3. Existing Decisions**

Read existing ADRs/PDRs to ensure consistency:

- `spx/{NN}-{slug}.adr.md` - Product-level ADRs (interleaved at root)
- `spx/{NN}-{slug}.pdr.md` - Product-level PDRs (interleaved at root)
- ADRs/PDRs interleaved within enabler/outcome nodes

</input_context>

<adr_scope>
You produce ADRs. The scope depends on what you're deciding:

| Decision Scope | ADR Location                                     | Example                                     |
| -------------- | ------------------------------------------------ | ------------------------------------------- |
| Product-wide   | `spx/{NN}-{slug}.adr.md`                         | "Use typed boundary errors across services" |
| Node-specific  | `spx/{NN}-{slug}.enabler/{NN}-{slug}.adr.md`     | "CLI command structure"                     |
| Nested node    | `spx/.../{NN}-{slug}.outcome/{NN}-{slug}.adr.md` | "Use tokio task orchestration for workers"  |

**ADR Numbering:**

- BSP range: [10, 99]
- Lower BSP = dependency (higher-BSP ADRs may rely on it)
- Insert using midpoint calculation: `new = floor((left + right) / 2)`
- Append using: `new = floor((last + 99) / 2)`
- First ADR in scope: use 21

See `/authoring` skill for complete ordering rules.

**Within-scope dependency order**: adr-21 must be decided before adr-37 (lower BSP = dependency).

**Cross-scope dependencies**: Must be documented explicitly in ADR "Context" section using markdown links.

</adr_scope>

<adr_creation_protocol>
Execute these phases IN ORDER.

**Phase 0: Read Context**

1. Read the node spec completely (requirements, assertions)
2. Read project context:
   - `spx/CLAUDE.md` - Project structure, navigation, work item management
3. Read `/standardizing-rust`, then `/standardizing-rust-architecture`
4. Read `spx/local/rust.md` and `spx/local/rust-architecture.md` if they exist
5. Read `/standardizing-rust-tests`, then `spx/local/rust-tests.md` if it exists
6. Invoke `/testing-rust` to understand testing methodology
7. Read existing ADRs for consistency:
   - `spx/{NN}-{slug}.adr.md` - Product-level ADRs
   - ADRs interleaved within enabler/outcome nodes
8. Read `/authoring` skill for ADR template

**Phase 1: Identify Decisions Needed**

For each TRD section, ask:

- What architectural choices does this imply?
- What patterns or approaches should be mandated?
- What constraints should be imposed?
- What trade-offs are being made?

List decisions needed before writing any ADRs.

**Phase 2: Analyze Rust-Specific Implications**

For each decision, consider:

- **Ownership model**: Who owns data? Where are borrowing boundaries? Is sharing really required?
- **Type system**: Which invariants belong in newtypes, type-state transitions, marker traits, or validated constructors?
- **Error model**: Where should the design use `Result`, `Option`, `thiserror`, `anyhow`, retries, or fail-fast behavior?
- **Concurrency model**: Is the workload sync, async, threaded, actor-like, or request-scoped? What `Send`/`Sync` constraints follow?
- **Resource lifecycle**: Where do RAII, `Drop`, pools, guards, or lazy initialization matter?
- **Ecosystem**: Which crates or runtime choices become architectural commitments?
- **Unsafe boundary**: Does the design introduce FFI, raw pointers, layout coupling, or soundness obligations?
- **Security**: What boundaries need protection?
- **Testability**: How will this be tested?

**Phase 3: Write ADRs**

Use the authoritative template (from `/understanding`). Each ADR includes:

1. **Purpose**: What concern this decision governs
2. **Context**: Business impact and technical constraints
3. **Decision**: The specific choice in one sentence
4. **Rationale**: Why this is right given constraints, alternatives rejected
5. **Trade-offs accepted**: What is given up, why acceptable
6. **Invariants** (optional): Algebraic properties for all governed code
7. **Compliance**: Recognized by, MUST rules, NEVER rules -- including testability constraints

**Phase 4: Verify Consistency**

- No ADR should contradict another
- Node ADRs must align with ancestor ADRs
- Nested ADRs must not contradict parent-level ADRs

</adr_creation_protocol>

<what_you_do_not_do>

1. **Do NOT write implementation code**. You write ADRs that constrain implementation.
2. **Do NOT review code**. That's a separate concern.
3. **Do NOT fix bugs**. That's an implementation concern.
4. **Do NOT create work items**. That's a project management concern.

</what_you_do_not_do>

<accessing_skill_files>
When this skill is invoked, Claude Code provides the base directory in the loading message:

```text
Base directory for this skill: {skill_dir}
```

Use this path to access skill files:

- References: `{skill_dir}/references/`

**IMPORTANT**: Do NOT search the project directory for skill files.
</accessing_skill_files>

<reference_index>
Detailed patterns and principles:

| File                            | Purpose                                                      |
| ------------------------------- | ------------------------------------------------------------ |
| `references/adr-patterns.md`    | Common ADR patterns for Rust                                 |
| `references/rust-principles.md` | Ownership, type-driven design, safety, lifecycle, and crates |

</reference_index>

<output_format>
When you complete ADR creation, provide:

```markdown
Architectural Decisions Created

ADRs Written

| ADR                                                         | Scope          | Decision Summary                                    |
| ----------------------------------------------------------- | -------------- | --------------------------------------------------- |
| [Error Architecture](spx/21-error-architecture.adr.md)      | Product        | Use typed boundary errors with explicit conversions |
| [CLI Structure](spx/32-cli.enabler/21-cli-structure.adr.md) | 32-cli enabler | Use `clap` derive and thin command handlers         |

Key Constraints

1. {constraint from [Error Architecture](spx/21-error-architecture.adr.md)}
2. {constraint from [CLI Structure](spx/32-cli.enabler/21-cli-structure.adr.md)}
```

</output_format>

<success_criteria>
ADR is complete when:

- [ ] Compliance section includes testability constraints (DI, no mocking) per `/standardizing-rust-architecture`
- [ ] `/standardizing-rust` was loaded before `/standardizing-rust-architecture`
- [ ] `/standardizing-rust-tests` was loaded before testing methodology was applied
- [ ] All architectural choices documented
- [ ] Compliance criteria defined with MUST/NEVER rules for verification
- [ ] No contradictions with existing ADRs
- [ ] Ownership, type-system, and resource-lifecycle considerations addressed
- [ ] Security boundaries identified

*Remember: Your decisions shape everything downstream. A well-designed architecture enables clean implementation.*
</success_criteria>

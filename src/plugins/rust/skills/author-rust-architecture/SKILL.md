---
name: author-rust-architecture
description: >-
  ALWAYS invoke this skill when writing ADRs for Rust.
  NEVER author a Rust ADR without this skill.
allowed-tools: Read, Write, Glob, Grep, {{! tool('use_skill') !}}
---

{!% require_skill 'rust:rust-code-standards' %!}

{!% require_skill 'rust:rust-architecture-standards' %!}

<objective>
A Rust ADR that follows the standard Rust architecture template, preserves spec-tree hierarchy constraints, and encodes testability as the architecture standard places it.
</objective>

<essential_principles>
**Standards are pre-loaded above.** The architecture standard owns the ADR sections and the placement of testability rules.

After reading those standards, check for `spx/local/rust.md` and `spx/local/rust-architecture.md` at the repository root. Read each file that exists and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.

- Prefer type-level invariants over runtime-only validation when the domain allows it
- Design around ownership, borrowing, and resource lifetimes explicitly
- Design for dependency injection (NO MOCKING)
- Produce ADRs (Architecture Decision Records), not implementation code

</essential_principles>

<context_loading>
**For spec-tree work items: Load complete context before creating ADRs.**

When creating ADRs for a spec-tree work item (enabler/outcome), ensure complete hierarchical context is loaded:

1. Use skill `spec-tree:contextualize` with the node path
2. **Verify all ancestor ADRs/PDRs are loaded** - Must understand and honor all decision records in hierarchy
3. **Read the node spec** - Requirements, Test Strategy, and Outcomes sections

**The `spec-tree:contextualize` skill provides:**

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Node spec with requirements, test strategy, and outcomes
- Typed assertions from the target node

**ADR creation requirements:**

- Must not contradict ancestor ADRs/PDRs (product → ancestor hierarchy)
- Must reference relevant ancestor decisions
- Must include testability constraints (DI, no mocking) where `rust:rust-architecture-standards` places them
- Must document trade-offs and consequences

**If NOT working on spec-tree work item**: Proceed directly with ADR creation using provided requirements.
</context_loading>

<input_context>
Before creating ADRs, understand:

**1. Node Specification**

- Functional requirements in `## Requirements` section
- Test strategy in `## Test Strategy` section
- Typed assertions from the node spec
- Architectural constraints from ancestor ADRs

**2. Product Context**

Read these files to understand product structure and workflow:

- `{{! file('root_guide') !}}` - Product navigation, work item status, BSP dependencies

For evidence routing, use skill `spec-tree:verify`. After test is selected, use skill `rust:rust-test-standards` and skill `rust:author-rust-test` for Rust expression.

**3. Existing Decisions**

Read existing ADRs/PDRs to ensure consistency:

- `spx/{NN}-{slug}.adr.md` - Product-level ADRs (interleaved at root)
- `spx/{NN}-{slug}.pdr.md` - Product-level PDRs (interleaved at root)
- ADRs/PDRs interleaved within enabler/outcome nodes

</input_context>

<adr_scope>
Produce ADRs. The scope depends on the decision:

| Decision Scope | ADR Location                                     | Example                                     |
| -------------- | ------------------------------------------------ | ------------------------------------------- |
| Product-wide   | `spx/{NN}-{slug}.adr.md`                         | "Use typed boundary errors across services" |
| Node-specific  | `spx/{NN}-{slug}.enabler/{NN}-{slug}.adr.md`     | "CLI command structure"                     |
| Nested node    | `spx/.../{NN}-{slug}.outcome/{NN}-{slug}.adr.md` | "Use tokio task orchestration for workers"  |

**ADR numbering and ordering:** Use skill `spec-tree:author` for BSP numbering and ordering rules. A lower BSP is a dependency of a higher one, so decide it first.

**Cross-scope dependencies**: Must be documented explicitly in the ADR decision statement or Rationale using markdown links.

</adr_scope>

<adr_creation_protocol>
Execute these phases IN ORDER.

**Phase 0: Read Context**

1. Read the node spec completely (requirements, assertions)
2. Read product context:
   - `{{! file('root_guide') !}}` - Product structure, navigation, work item management
3. Read `spx/local/rust.md` and `spx/local/rust-architecture.md` if they exist
4. Use skill `rust:rust-test-standards`, then read `spx/local/rust-tests.md` if it exists
5. Use skill `spec-tree:verify` for evidence routing; after test is selected, use skill `rust:author-rust-test` for Rust expression
6. Read existing ADRs for consistency:
   - `spx/{NN}-{slug}.adr.md` - Product-level ADRs
   - ADRs interleaved within enabler/outcome nodes
7. Use skill `spec-tree:author` for the ADR template

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

Use skill `spec-tree:understand` for the authoritative ADR template, and apply `rust:rust-architecture-standards` for the sections and the testability rules. Fill each section with the Rust-specific decisions identified in Phase 2.

**Phase 4: Verify Consistency**

- No ADR contradicts another
- Node ADRs must align with ancestor ADRs
- Nested ADRs must not contradict parent-level ADRs

</adr_creation_protocol>

<out_of_scope>

1. **Do NOT write implementation code**. ADRs constrain implementation; they are not it.
2. **Do NOT review code**. That's a separate concern.
3. **Do NOT fix bugs**. That's an implementation concern.
4. **Do NOT create work items**. That's a product management concern.

</out_of_scope>

<reference_index>
Detailed patterns and principles:

| File                                                | Purpose                                   |
| --------------------------------------------------- | ----------------------------------------- |
| `${CLAUDE_SKILL_DIR}/references/adr-patterns.md`    | Common ADR patterns for Rust              |
| `${CLAUDE_SKILL_DIR}/references/rust-principles.md` | Decisions an ADR records per Rust concern |

</reference_index>

<output_format>
When ADR creation is complete, provide:

```markdown
Architectural Decisions Created

ADRs Written

| ADR                                | Scope   | Decision Summary            |
| ---------------------------------- | ------- | --------------------------- |
| [{ADR Name}]({path to ADR})        | {scope} | {one-line decision summary} |
| [{Second ADR Name}]({path to ADR}) | {scope} | {one-line decision summary} |

Key Constraints

1. {constraint from [{ADR Name}]({path to ADR})}
2. {constraint from [{Second ADR Name}]({path to ADR})}
```

</output_format>

<success_criteria>
ADR is complete when:

- [ ] Testability constraints (DI, no mocking) are recorded per `rust:rust-architecture-standards`
- [ ] `rust:rust-code-standards` was loaded before `rust:rust-architecture-standards`
- [ ] `rust:rust-test-standards` was loaded before testing methodology was applied
- [ ] All architectural choices documented
- [ ] Verification rules defined as ALWAYS/NEVER guarantees and boundaries
- [ ] No contradictions with existing ADRs
- [ ] Ownership, type-system, and resource-lifecycle considerations addressed
- [ ] Security boundaries identified

</success_criteria>

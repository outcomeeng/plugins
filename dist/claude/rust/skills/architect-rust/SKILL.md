---
name: architect-rust
description: ALWAYS invoke this skill when writing ADRs for Rust.
allowed-tools: Read, Write, Glob, Grep, Skill
---

Invoke the `rust:rust-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `rust:rust-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

<objective>
A Rust ADR that follows the standard Rust architecture template, preserves spec-tree hierarchy constraints, and encodes testability as `## Verification` `### Audit` rules.
</objective>

<essential_principles>
**Standards are pre-loaded above.** The first skill defines shared Rust standards; the architecture standard defines canonical ADR sections, how testability appears in `## Verification` `### Audit` rules, and what does not belong in an ADR.

After reading those standards, check for `spx/local/rust.md` and `spx/local/rust-architecture.md` at the repository root. Read each file that exists and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.

- ADRs follow the authoritative template: title + decision stated directly, Rationale, Invariants (optional), Verification
- Testability constraints go under `## Verification`'s `### Audit` subsection as ALWAYS/NEVER rules -- not in a separate Testing Strategy section
- Prefer type-level invariants over runtime-only validation when the domain allows it
- Design around ownership, borrowing, and resource lifetimes explicitly
- Design for dependency injection (NO MOCKING)
- Produce ADRs (Architecture Decision Records), not implementation code

</essential_principles>

<context_loading>
**For spec-tree work items: Load complete context before creating ADRs.**

When creating ADRs for a spec-tree work item (enabler/outcome), ensure complete hierarchical context is loaded:

1. **Invoke `spec-tree:contextualize`** with the node path
2. **Verify all ancestor ADRs/PDRs are loaded** - Must understand and honor all decision records in hierarchy
3. **Read the node spec** - Requirements, Test Strategy, and Outcomes sections

**The `spec-tree:contextualize` skill provides:**

- Complete ADR/PDR hierarchy (product and ancestor decisions at all levels)
- Node spec with requirements, test strategy, and outcomes
- Typed assertions from the target node

**ADR creation requirements:**

- Must not contradict ancestor ADRs/PDRs (product → ancestor hierarchy)
- Must reference relevant ancestor decisions
- Must include testability constraints in `## Verification` (`### Audit` ALWAYS/NEVER rules for DI, no mocking)
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

- `CLAUDE.md` - Product navigation, work item status, BSP dependencies

For evidence routing, invoke `/verify`. After test is selected, read `/rust-test-standards` and invoke `/test-rust` for Rust expression.

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

**ADR Numbering:**

- BSP range: [10, 99]
- Lower BSP = dependency (higher-BSP ADRs may rely on it)
- Insert using midpoint calculation: `new = floor((left + right) / 2)`
- Append using: `new = floor((last + 99) / 2)`
- First ADR in scope: use 21

See `/author` skill for complete ordering rules.

**Within-scope dependency order**: adr-21 must be decided before adr-37 (lower BSP = dependency).

**Cross-scope dependencies**: Must be documented explicitly in the ADR decision statement or Rationale using markdown links.

</adr_scope>

<adr_creation_protocol>
Execute these phases IN ORDER.

**Phase 0: Read Context**

1. Read the node spec completely (requirements, assertions)
2. Read product context:
   - `CLAUDE.md` - Product structure, navigation, work item management
3. Read `/rust-standards`, then `/rust-architecture-standards`
4. Read `spx/local/rust.md` and `spx/local/rust-architecture.md` if they exist
5. Read `/rust-test-standards`, then `spx/local/rust-tests.md` if it exists
6. Invoke `/verify` for evidence routing; after test is selected, invoke `/test-rust` for Rust expression
7. Read existing ADRs for consistency:
   - `spx/{NN}-{slug}.adr.md` - Product-level ADRs
   - ADRs interleaved within enabler/outcome nodes
8. Read `/author` skill for ADR template

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

Use the authoritative template (from `/understand`). The ADR is decision-first:

1. **Title + decision**: `# {Decision Name}`, then the decision stated directly as permanent truth in 1-3 sentences -- what it governs and what it decides. No `Purpose` heading, no `Context` section; business impact and constraints fold into the decision statement and Rationale
2. **Rationale**: Why this is right given the constraints; name a rejected alternative only when it sharpens the decision
3. **Invariants** (optional): Algebraic properties for all governed code
4. **Verification**: ALWAYS/NEVER rules grouped under `### Testing` (`[{assertion type}]`), `### Eval` (`[eval]`), `### Audit` (`[audit]`), ordered by decreasing enforcement strength; the DI/mocking testability constraints are `### Audit` rules carrying `([audit])`

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

<accessing_skill_files>
When this skill is invoked, the skill loader provides the base directory in the loading message:

```text
Base directory for this skill: ${CLAUDE_SKILL_DIR}
```

Use this path to access skill files:

- References: `${CLAUDE_SKILL_DIR}/references/`

**IMPORTANT**: Do NOT search the product directory for skill files.
</accessing_skill_files>

<reference_index>
Detailed patterns and principles:

| File                                                | Purpose                                                      |
| --------------------------------------------------- | ------------------------------------------------------------ |
| `${CLAUDE_SKILL_DIR}/references/adr-patterns.md`    | Common ADR patterns for Rust                                 |
| `${CLAUDE_SKILL_DIR}/references/rust-principles.md` | Ownership, type-driven design, safety, lifecycle, and crates |

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

- [ ] Verification (`### Audit`) includes testability constraints (DI, no mocking) per `/rust-architecture-standards`
- [ ] `/rust-standards` was loaded before `/rust-architecture-standards`
- [ ] `/rust-test-standards` was loaded before testing methodology was applied
- [ ] All architectural choices documented
- [ ] Verification rules defined as ALWAYS/NEVER guarantees and boundaries
- [ ] No contradictions with existing ADRs
- [ ] Ownership, type-system, and resource-lifecycle considerations addressed
- [ ] Security boundaries identified

</success_criteria>

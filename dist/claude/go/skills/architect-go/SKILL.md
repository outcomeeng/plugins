---
name: architect-go
description: ALWAYS invoke this skill when writing ADRs for Go.
allowed-tools: Read, Write, Glob, Grep, Skill
---

Invoke the `go:go-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `go:go-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A Go ADR authored to the decision template the `/understand` foundation provides, that preserves spec-tree hierarchy constraints, and encodes testability as `## Verification` `### Audit` rules.
</objective>

<essential_principles>
**Standards are pre-loaded above.** The first skill defines shared Go standards; the architecture standard names the decision template as the source of the ADR's shape, how testability appears in `## Verification` `### Audit` rules, and what does not belong in an ADR.

After reading those standards, check for `spx/local/go.md` and `spx/local/go-architecture.md` at the repository root. Read each file that exists and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.

- ADRs take their shape from the decision template loaded through the live `/understand` foundation; no skill restates it
- Testability constraints go under `## Verification`'s `### Audit` subsection as ALWAYS/NEVER rules -- not in a separate Testing Strategy section
- Prefer type-level invariants and validating constructors over runtime-only checks when the domain allows it
- Design around package boundaries, `internal/` visibility, goroutine ownership, and context propagation explicitly
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

- `CLAUDE.md` - Product navigation, work item status, sparse integer index dependencies

For evidence routing, invoke `/verify`. After test is selected, read `/go-test-standards` and invoke `/test-go` for Go expression.

**3. Existing Decisions**

Read existing ADRs/PDRs to ensure consistency:

- `spx/{NN}-{slug}.adr.md` - Product-level ADRs (interleaved at root)
- `spx/{NN}-{slug}.pdr.md` - Product-level PDRs (interleaved at root)
- ADRs/PDRs interleaved within enabler/outcome nodes

</input_context>

<adr_scope>
Produce ADRs. The scope depends on the decision:

| Decision Scope | ADR Location                                     | Example                                          |
| -------------- | ------------------------------------------------ | ------------------------------------------------ |
| Product-wide   | `spx/{NN}-{slug}.adr.md`                         | "Wrap every boundary error with %w"              |
| Node-specific  | `spx/{NN}-{slug}.enabler/{NN}-{slug}.adr.md`     | "CLI command structure"                          |
| Nested node    | `spx/.../{NN}-{slug}.outcome/{NN}-{slug}.adr.md` | "Use errgroup-owned workers for the ingest loop" |

**ADR Numbering:**

- Sparse integer index range: [10, 99]
- Lower sparse integer index = dependency (higher-index ADRs may rely on it)
- Insert using midpoint calculation: `new = floor((left + right) / 2)`
- Append using: `new = floor((last + 99) / 2)`
- First ADR in scope: use 21

See `/author` skill for complete ordering rules.

**Within-scope dependency order**: adr-21 must be decided before adr-37 (lower sparse integer index = dependency).

**Cross-scope dependencies**: Must be documented explicitly in the ADR decision statement or Rationale using markdown links.

</adr_scope>

<adr_creation_protocol>
Execute these phases IN ORDER.

**Phase 0: Read Context**

1. Read the node spec completely (requirements, assertions)
2. Read product context:
   - `CLAUDE.md` - Product structure, navigation, work item management
3. Read `/go-standards`, then `/go-architecture-standards`
4. Read `spx/local/go.md` and `spx/local/go-architecture.md` if they exist
5. Read `/go-test-standards`, then `spx/local/go-tests.md` if it exists
6. Invoke `/verify` for evidence routing; after test is selected, invoke `/test-go` for Go expression
7. Read existing ADRs for consistency:
   - `spx/{NN}-{slug}.adr.md` - Product-level ADRs
   - ADRs interleaved within enabler/outcome nodes
8. Load the decision template through the live `/understand` foundation

**Phase 1: Identify Decisions Needed**

For each TRD section, ask:

- What architectural choices does this imply?
- What patterns or approaches should be mandated?
- What constraints should be imposed?
- What trade-offs are being made?

List decisions needed before writing any ADRs.

**Phase 2: Analyze Go-Specific Implications**

For each decision, consider:

- **Package model**: Which packages own the concern? What stays under `internal/`? Where are interfaces consumed?
- **Type system**: Which invariants belong in defined types, typed constant sets, or validating constructors?
- **Error model**: Which failures are sentinel errors, which carry data in error structs, where does `%w` wrapping stop, and what is user-facing?
- **Concurrency model**: Is the workload synchronous, goroutine-per-request, worker-pool, or pipeline? Who owns each goroutine, and how does `context.Context` cancel it?
- **Resource lifecycle**: Where do `Close` methods, `defer`, pools, and `sync.Once` initialization matter?
- **Ecosystem**: Which modules or runtime choices become architectural commitments?
- **Unsafe boundary**: Does the design introduce cgo, `unsafe.Pointer`, or layout coupling?
- **Security**: What boundaries need protection?
- **Testability**: How will this be tested?

**Phase 3: Write ADRs**

Load the decision template through the live `/understand` foundation and author to it. The template settles the sections and their order; `/go-architecture-standards` `<template_source>` and `<testability_in_verification>` settle the Go placement: the DI/mocking testability constraints are `## Verification` `### Audit` rules carrying `([audit])`, and Go architecture rules that need agent judgment carry the same tag.

**Phase 4: Verify Consistency**

- No ADR contradicts another
- Node ADRs must align with ancestor ADRs
- Nested ADRs must not contradict parent-level ADRs

</adr_creation_protocol>

<out_of_scope>

1. NEVER write implementation code — ADRs constrain implementation; they are not it.
2. NEVER review code — that is a separate concern.
3. NEVER fix bugs — that is an implementation concern.
4. NEVER create work items — that is a product management concern.

</out_of_scope>

<reference_index>
Detailed patterns and principles:

| File                                              | Purpose                                                        |
| ------------------------------------------------- | -------------------------------------------------------------- |
| `${CLAUDE_SKILL_DIR}/references/adr-patterns.md`  | Common ADR patterns for Go                                     |
| `${CLAUDE_SKILL_DIR}/references/go-principles.md` | Packages, type-driven design, errors, concurrency, and modules |

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

- [ ] Verification (`### Audit`) includes testability constraints (DI, no mocking) per `/go-architecture-standards`
- [ ] Every Verification rule cites a Go seam, type, error, concurrency, or lifecycle constraint `/go-standards` names, in Go terms
- [ ] Every test-level reference in the ADR matches the level vocabulary `/go-test-standards` declares
- [ ] All architectural choices documented
- [ ] Verification rules defined as ALWAYS/NEVER guarantees and boundaries
- [ ] No contradictions with existing ADRs
- [ ] Package, type-system, concurrency, and resource-lifecycle considerations addressed
- [ ] Security boundaries identified

</success_criteria>

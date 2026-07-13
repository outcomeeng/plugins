---
name: architect-typescript
description: >-
  ALWAYS invoke this skill when writing ADRs for TypeScript.
allowed-tools: Read, Write, Glob, Grep, Skill
---

{!% require_skill 'typescript:typescript-architecture-standards' %!}

<objective>
A binding TypeScript ADR whose testability constraints live as ALWAYS/NEVER rules under the `## Verification` section's `### Audit` subsection.
</objective>

<essential_principles>
**Standards are pre-loaded above.** Check for `spx/local/typescript-architecture.md` at the repository root and read it if it exists, applying it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.

- ADRs follow the authoritative template: title + decision stated directly, Rationale (optional), Invariants (optional), Verification
- Testability constraints go under `## Verification`'s `### Audit` subsection as ALWAYS/NEVER rules -- not in a separate Testing Strategy section
- No `any` without explicit justification in ADR
- Design for dependency injection (NO MOCKING)
- Produce ADRs (Architecture Decision Records), not implementation code

</essential_principles>

<context_loading>
**For spec-tree work items: Load complete context before creating ADRs.**

When creating ADRs for a spec-tree work item (enabler/outcome), ensure complete hierarchical context is loaded:

1. **Invoke `/contextualize`** with the node path
2. **Verify all ancestor ADRs/PDRs are loaded** - Must understand and honor all decision records in hierarchy
3. **Read the node spec** - Requirements, Test Strategy, and Outcomes sections

**The `/contextualize` skill provides:**

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

- `{{! file('root_guide') !}}` - Product navigation, work item status, sparse integer index dependencies

For TypeScript test standards and methodology, invoke `/typescript-test-standards` and `/test-typescript`

**3. Existing Decisions**

Read existing ADRs/PDRs to ensure consistency:

- `spx/{NN}-{slug}.adr.md` - Product-level ADRs (interleaved at root)
- `spx/{NN}-{slug}.pdr.md` - Product-level PDRs (interleaved at root)
- ADRs/PDRs interleaved within enabler/outcome nodes

</input_context>

<adr_scope>
Produce ADRs. The scope depends on the decision:

| Decision Scope | ADR Location                                     | Example                              |
| -------------- | ------------------------------------------------ | ------------------------------------ |
| Product-wide   | `spx/{NN}-{slug}.adr.md`                         | "Use Zod for all data validation"    |
| Node-specific  | `spx/{NN}-{slug}.enabler/{NN}-{slug}.adr.md`     | "CLI command structure"              |
| Nested node    | `spx/.../{NN}-{slug}.outcome/{NN}-{slug}.adr.md` | "Use execa for subprocess execution" |

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
   - `{{! file('root_guide') !}}` - Product structure, navigation, work item management
3. Read `/typescript-architecture-standards` for canonical ADR conventions
4. Invoke `/typescript-test-standards` for canonical test standards
5. Invoke `/test-typescript` for TypeScript testing methodology and patterns
6. Read existing ADRs for consistency:
   - `spx/{NN}-{slug}.adr.md` - Product-level ADRs
   - ADRs interleaved within enabler/outcome nodes
7. Use the loaded `/typescript-architecture-standards` `<adr_sections>` contract as the canonical ADR section shape; invoke `/author` only when placement or sparse ordering must be determined

**Phase 1: Identify Decisions Needed**

For each requirement and typed assertion in the node spec, ask:

- What architectural choices does this imply?
- What patterns or approaches should be mandated?
- What constraints should be imposed?
- What trade-offs are being made?

List decisions needed before writing any ADRs.

**Phase 2: Analyze TypeScript-Specific Implications**

For each decision, consider:

- **Type system**: How will types be designed? What generics needed?
- **Architecture**: Which pattern applies (DDD, hexagonal, etc.)?
- **Security**: What boundaries need protection?
- **Testability**: How will this be tested?

**Phase 3: Write ADRs**

Use the canonical section contract from `/typescript-architecture-standards` `<adr_sections>`, which derives from the `/understand` ADR template. The ADR is decision-first:

1. **Title + decision**: `# {Decision Name}`, then the decision stated directly as permanent truth in 1-3 sentences -- what it governs and what it decides. No `Purpose` heading, no `Context` section; business impact and constraints fold into the decision statement and Rationale
2. **Rationale** (optional): Why this is right given the constraints; name a rejected alternative only when it sharpens the decision
3. **Invariants** (optional): Algebraic properties for all governed code
4. **Verification**: ALWAYS/NEVER rules grouped under `### Testing` (`[{assertion type}]`), `### Eval` (`[eval]`), `### Audit` (`[audit]`), ordered by decreasing enforcement strength; the DI/mocking testability constraints are `### Audit` rules carrying `([audit])`

**Phase 4: Verify Consistency**

- No ADR should contradict another
- Node ADRs must align with ancestor ADRs
- Nested ADRs must not contradict parent-level ADRs

</adr_creation_protocol>

<verification_gates>

**Gate 1 — context and decision inventory, before Phase 3:**

- PASS only when a live context receipt matches the target node, every product and ancestor ADR/PDR listed by that context has been read, the `/typescript-architecture-standards` `<adr_sections>` contract is loaded, and the decisions needed are listed.
- FAIL when any receipt, governing decision, section contract, or decision-list entry is absent; stop before drafting and load the missing material.

**Gate 2 — artifact consistency, before reporting completion:**

- PASS only when every written ADR has a direct decision statement plus the permitted optional Rationale, optional Invariants, and required Verification sections; `## Verification` contains `### Audit` testability rules for DI and no mocking; every cited decision uses its full `spx/...` path; and a comparison against every loaded governing decision finds no contradiction.
- FAIL when a required section or audit rule is absent, an unpermitted section is present, a citation is ambiguous, or any governing decision conflicts; repair the ADR and repeat this gate.

</verification_gates>

<out_of_scope>

1. **Do NOT write implementation code**. ADRs constrain implementation; they are not it.
2. **Do NOT review code**. That's a separate concern.
3. **Do NOT fix bugs**. That's an implementation concern.
4. **Do NOT create work items**. That's a product management concern.

</out_of_scope>

<accessing_skill_files>
When this skill is invoked, the runtime provides the skill base directory in the loading message:

```
Base directory for this skill: ${CLAUDE_SKILL_DIR}
```

Use this path to access skill files:

- References: `${CLAUDE_SKILL_DIR}/references/`

**IMPORTANT**: Do NOT search the product directory for skill files.
</accessing_skill_files>

<reference_index>
Detailed patterns and principles:

| File                                                      | Purpose                                   |
| --------------------------------------------------------- | ----------------------------------------- |
| `${CLAUDE_SKILL_DIR}/references/adr-patterns.md`          | Common ADR patterns for TypeScript        |
| `${CLAUDE_SKILL_DIR}/references/typescript-principles.md` | Type safety, clean architecture, security |

</reference_index>

<output_format>
When ADR creation is complete, provide:

```markdown
**Architectural Decisions Created**

**ADRs Written**

| ADR                                | Scope   | Decision Summary            |
| ---------------------------------- | ------- | --------------------------- |
| [{ADR Name}]({path to ADR})        | {scope} | {one-line decision summary} |
| [{Second ADR Name}]({path to ADR}) | {scope} | {one-line decision summary} |

**Key Constraints**

1. {constraint from [{ADR Name}]({path to ADR})}
2. {constraint from [{Second ADR Name}]({path to ADR})}
```

</output_format>

<success_criteria>
ADR is complete when:

- [ ] Every ADR contains a direct decision statement and `## Verification`; `## Rationale` and `## Invariants` appear only when applicable, and no other sections appear
- [ ] `## Verification` contains `### Audit` rules that state DI and no-mocking testability boundaries as ALWAYS/NEVER guarantees carrying `([audit])`
- [ ] Each type-system, architecture, security, and testability question identified in Phase 2 is answered in the decision or Rationale, or recorded as not applicable there
- [ ] Every governing-decision citation uses a full `spx/...` path, and the final comparison records no contradiction with loaded product or ancestor decisions
- [ ] The completion report lists every written ADR path, scope, decision summary, and resulting constraint

</success_criteria>

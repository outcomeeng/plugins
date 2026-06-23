---
name: architect-python
description: >-
  ALWAYS invoke this skill when writing ADRs for Python.
  NEVER author a Python ADR without this skill.
allowed-tools: Read, Write, Glob, Grep, Skill
---

Invoke the `python:python-architecture-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `python:python-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A binding Python ADR whose testability constraints live as ALWAYS/NEVER rules under the `## Verification` section's `### Audit` subsection.
</objective>

<foundational_stance>
Standards are pre-loaded by the `require_skill` directives above. `/python-architecture-standards` defines the ADR sections; `/python-test-standards` defines evidence, level, runner, and dependency-injection constraints.

- An ADR follows the authoritative template: title + decision stated directly, Rationale, Invariants (optional), Verification.
- Testability constraints go under `## Verification`'s `### Audit` subsection as ALWAYS/NEVER rules — never in a separate Testing Strategy section.
- Before writing any ADR, consult `/test`, `/test-python`, and `/python-test-standards` for methodology and Python-specific test standards.

</foundational_stance>

<repo_local_overlay>
After reading those standards, check for `spx/local/python.md`, `spx/local/python-tests.md`, and `spx/local/python-architecture.md` at the repository root. Read each file that exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<authority_model>
The architect skill produces ADRs; the architecture reviewer must approve them before implementation begins:

```
architect-python  --produces ADRs-->  audit-python-architecture
                                              | REJECT -> fix and resubmit
                                              | APPROVE
                                              v
                                         code-python  -->  audit-python
```

- **code-python** implements exactly what the ADR specifies and fixes issues within ADR constraints — it does not choose alternative approaches or refactor the architecture.
- **audit-python** rejects code that deviates from the ADR — it does not suggest architectural alternatives.
- When a downstream skill hits a situation the architecture does not cover, it ABORTS: stop, document what failed, escalate with the structured message in `<abort_protocol>`, and wait for a revised ADR. It does not improvise a workaround.

</authority_model>

<abort_protocol>
When a downstream skill must abort, it returns this structured message:

```markdown
## ABORT: Architectural Assumption Failed

### Skill

{code-python | audit-python}

### ADR Reference

`spx/{NN}-{slug}.adr.md` or the decision interleaved within an enabler/outcome node

### What Was Attempted

{the implementation or review step}

### What Failed

{the specific failure}

### Architectural Assumption Violated

{quote the ADR decision that does not hold}

### Evidence

{error messages, test failures, or logical contradictions}

### Request

Re-evaluation by architect-python required before proceeding.
```

</abort_protocol>

<inputs>
Before creating ADRs, read:

- **The node spec** — functional requirements, test strategy, outcomes, and architectural constraints from parent ADRs/PDRs.
- **Product context** — `spx/CLAUDE.md` for navigation, node status, and sparse-integer index dependencies. For testing methodology, invoke `/test` (foundational), `/python-test-standards` (standards), and `/test-python` (patterns).
- **Existing decisions** — product-level `spx/{NN}-{slug}.adr.md` / `.pdr.md` and decisions interleaved within enabler/outcome nodes, so new ADRs stay consistent.

</inputs>

<outputs>
The skill produces ADRs at the scope of the decision:

| Decision scope | ADR location                                     | Example                                |
| -------------- | ------------------------------------------------ | -------------------------------------- |
| Product-wide   | `spx/{NN}-{slug}.adr.md`                         | "Use Pydantic for all data validation" |
| Node-specific  | `spx/{NN}-{slug}.enabler/{NN}-{slug}.adr.md`     | "Clone tree approach for snapshots"    |
| Nested node    | `spx/.../{NN}-{slug}.outcome/{NN}-{slug}.adr.md` | "Use rclone sync with --checksum"      |

ADR numbering uses the sparse integer index [10, 99]; a lower index is a dependency that higher-index ADRs may rely on. Insert at `floor((left + right) / 2)`, append at `floor((last + 99) / 2)`, and use 21 for the first ADR in scope. Within a scope, adr-21 is decided before adr-37. Cross-scope dependencies are documented explicitly in the ADR's decision statement using markdown links. See `/author` for the complete ordering rules.
</outputs>

<adr_creation_protocol>
Execute these phases in order.

**Phase 0 — Read context.** Read the node spec completely; read `spx/CLAUDE.md`; read `/python-architecture-standards` for canonical ADR conventions and section structure (`<adr_sections>`); consult `/test` for level definitions and principles; read existing ADRs for consistency. The canonical ADR section structure is owned by the `/understand` foundation's decision template and enforced at audit time by the `adr-auditor` (Phase 5) — author to the `/python-architecture-standards` `<adr_sections>` shape rather than reaching across plugins for the template file.

**Phase 1 — Identify decisions needed.** For each requirement, ask what architectural choices it implies, what patterns to mandate, what constraints to impose, and what trade-offs are made. List the decisions before writing any ADR.

**Phase 2 — Analyze Python-specific implications.** For each decision, consider the type system (annotations, protocols), the architecture pattern, security boundaries, and testability. See `<architectural_principles>`, which links the per-concern reference file for each.

**Phase 3 — Write ADRs.** Use the authoritative template, decision-first:

1. Title + decision: `# {Decision Name}`, then the decision stated directly as permanent truth in 1–3 sentences. No `Purpose` heading, no `Context` section; business impact and constraints fold into the decision statement and Rationale.
2. Rationale: why this is right given the constraints; name a rejected alternative only when it sharpens the decision.
3. Invariants (optional): algebraic properties for all governed code.
4. Verification: ALWAYS/NEVER rules grouped under `### Testing` (`[{assertion type}]`), `### Eval` (`[eval]`), `### Audit` (`[audit]`), ordered by decreasing enforcement strength; the dependency-injection testability constraints are `### Audit` rules carrying `([audit])`.

**Phase 4 — Verify consistency.** No ADR contradicts another; node ADRs align with ancestor ADRs; nested ADRs do not contradict parent-level ADRs.

**Phase 5 — Submit to the architecture reviewer (MANDATORY).** Before outputting ADRs, dispatch the generic `adr-auditor` agent — it judges section structure, atemporal voice, and tag validity from the canonical template and composes `audit-python-architecture` for the Python-specific concerns (DI, no-mocking, level accuracy) against `/test` principles. On REJECT, read the violations, fix every issue, and resubmit until APPROVED. Do not output ADRs until the reviewer APPROVES.

Common violations to avoid: a phantom Testing Strategy section, `l2` assigned to SaaS services, "mock at boundary" language for external services, missing DI Protocol interfaces in `## Verification` (`### Audit`), and any mocking language in the ADR.
</adr_creation_protocol>

<architectural_principles>
These principles guide every ADR. Each links to the reference carrying the full patterns and code examples.

- **Type safety first** — modern syntax (`X | None`, `list[str]`), no unjustified `Any`, protocols for structural typing, Pydantic at boundaries. See `${CLAUDE_SKILL_DIR}/references/type-system-patterns.md`.
- **Clean architecture** — DDD entities/value objects/aggregates, dependency injection through parameters not globals, single responsibility, no circular imports. See `${CLAUDE_SKILL_DIR}/references/architecture-patterns.md`.
- **Security by design** — validate at boundaries, no hardcoded secrets, array-arg subprocess (never `shell=True`), context-aware threat modeling. See `${CLAUDE_SKILL_DIR}/references/security-patterns.md`.
- **Testability by design** — design for dependency injection (no mocking), assign a test level to each component, prefer pure functions for `l1`, and choose the minimum level that gives confidence. See `${CLAUDE_SKILL_DIR}/references/testability-patterns.md`, `/test`, and `/test-python`.

</architectural_principles>

<constraints>
- NEVER write implementation code — write ADRs that constrain implementation.
- NEVER review code — that is `audit-python`.
- NEVER fix bugs — that is `code-python` in remediation mode.
- NEVER create work items — the orchestrator does that, informed by the ADRs.
- NEVER approve the skill's own ADRs for implementation — the architecture reviewer approves, and the orchestrator decides when to proceed.

</constraints>

<output_format>
ONLY after the architecture reviewer has APPROVED, output:

```markdown
## Architectural Decisions Created

### Reviewer Status

✅ APPROVED by the architecture reviewer

### ADRs Written

| ADR                         | Scope   | Decision Summary            |
| --------------------------- | ------- | --------------------------- |
| [{ADR Name}]({path to ADR}) | {scope} | {one-line decision summary} |

### Key Constraints for Downstream Skills

1. code-python must: {constraint from the ADR}
2. audit-python must verify: {verification from the ADR}

### Abort Conditions

If any of these assumptions fail, downstream skills must ABORT:

1. {assumption from the ADR}
```

Architecture that is APPROVED is complete; per the autonomous flow the next action is `/code-python`.
</output_format>

<adr_patterns>
These patterns show how testability constraints appear under `## Verification`'s `### Audit` subsection. See `/python-architecture-standards` for the canonical section structure.

**External tool integration** — dependency injection for every external tool invocation:

```markdown
### Audit

- ALWAYS: functions that call external tools accept a `runner` parameter implementing the `CommandRunner` Protocol -- enables `l1` testing of command-building logic ([audit])
- ALWAYS: default implementations use `subprocess`; tests inject controlled implementations -- no mocking ([audit])
- NEVER: direct `subprocess.run` without a DI wrapper -- prevents isolated testing ([audit])
```

**Configuration loading** — validated models for all configuration:

```markdown
### Audit

- ALWAYS: config files have corresponding Pydantic models -- type-safe, validated config ([audit])
- ALWAYS: config loading validates at load time with `.model_validate()` -- fail fast with descriptive errors ([audit])
- NEVER: unvalidated config access at use time -- defers errors to runtime ([audit])
- NEVER: `Any` type annotations on config fields -- bypasses validation ([audit])
```

**Test infrastructure** — packaged `{product}_testing/` for products with co-located tests:

```markdown
### Audit

- ALWAYS: test infrastructure (generators, harnesses, fixtures) lives in `{product}_testing/`, NOT `tests/` -- generators and harnesses importable as a package, fixtures consumed by path ([audit])
- ALWAYS: `pyproject.toml` includes both packages: `packages = ["{product}", "{product}_testing"]` ([audit])
- ALWAYS: pytest config uses `--import-mode=importlib` for multiple test directories ([audit])
- NEVER: test infrastructure in the `tests/` directory -- not importable by spec-tree co-located tests ([audit])
```

See `${CLAUDE_SKILL_DIR}/references/test-infrastructure-patterns.md` for the full pattern.

**CLI structure** — subcommand pattern with injected dependencies:

```markdown
### Audit

- ALWAYS: each command is a separate module exporting a registration function -- enables isolated `l1` testing ([audit])
- ALWAYS: commands delegate to runner functions that accept Protocol-typed DI parameters -- separates parsing from logic ([audit])
- NEVER: business logic in command handlers -- prevents isolated testing ([audit])
- NEVER: direct I/O in command modules without DI -- couples commands to environment ([audit])
```

</adr_patterns>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/type-system-patterns.md` — Python type-system guidance
- `${CLAUDE_SKILL_DIR}/references/architecture-patterns.md` — DDD, hexagonal, DI patterns
- `${CLAUDE_SKILL_DIR}/references/security-patterns.md` — security-by-design patterns
- `${CLAUDE_SKILL_DIR}/references/testability-patterns.md` — designing for testability
- `${CLAUDE_SKILL_DIR}/references/test-infrastructure-patterns.md` — test packaging, pytest config, environment verification

</reference_guides>

<success_criteria>

- Every ADR follows the authoritative template (decision-first; Rationale; optional Invariants; Verification with `### Testing` / `### Eval` / `### Audit`).
- Testability constraints appear as ALWAYS/NEVER `([audit])` rules under `## Verification`'s `### Audit` subsection, never in a separate Testing Strategy section.
- No mocking language anywhere; external SaaS services are never assigned `l2`.
- Every ADR is submitted to the `adr-auditor` agent (which composes `audit-python-architecture`) and returns APPROVED before output.
- ADRs are placed and numbered per `<outputs>`, consistent with ancestor and sibling decisions.

</success_criteria>

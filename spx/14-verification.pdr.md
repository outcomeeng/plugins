# Verification

This product adopts the verification taxonomy declared in the `/understand` foundation's verification-kinds reference: five types — validation, testing, reviewing, auditing, evaluating — across two orthogonal axes, verdict mode (deterministic / agentic) and purpose (conformance / correctness). Three types back the tag an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing.

## Rationale

This product adopts the marketplace verification taxonomy rather than defining its own, so every node's evidence reads the same way across the spec tree and the two agentic types — auditing and reviewing — are themselves verified by graded eval cases. An audit verdict is produced in an isolated agent context, reached only by dispatching the corresponding auditor agent, so the judgment stays free of the bias the main conversation accumulates while doing the work under audit. The rule binds the main conversation's entry point; a dispatched agent's own calls while it runs the audit are a separate concern.

## Product properties

1. Verification is the five marketplace types — validation, testing, reviewing, auditing, evaluating — across two axes, verdict mode and purpose. Three back the tag an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing.
2. Each path-bearing evidence link resolves to its target — a `[test]` link to an executable test, an `[eval]` link to an eval definition — and the `[audit]` tag is pathless.
3. An audit verdict is produced in an isolated agent context, reached only by dispatching the corresponding auditor agent. The main conversation never invokes an audit skill in place to produce a verdict.

## Verification

### Audit

- ALWAYS: an activity declares its type and purpose ([audit])
- NEVER: a type's verdict mode differs from the one its definition binds — the binding is fixed, not chosen per run ([audit])
- NEVER: a model judges the verdict of a deterministic type — it may run inside the process, but the verdict is the deterministic score ([audit])
- ALWAYS: the main conversation produces an audit verdict only by dispatching the corresponding auditor agent — the auditor agent's isolated context is the surface that emits the verdict ([audit])
- NEVER: the main conversation invokes an audit skill in place to produce a verdict — direct in-context invocation reintroduces the bias the dispatched agent's isolated context removes ([audit])
- NEVER: the type set or the two verdict modes are extended — a new type amends the `/understand` foundation's verification-kinds reference and this decision ([audit])

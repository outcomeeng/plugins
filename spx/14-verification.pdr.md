# Verification

This product adopts the verification taxonomy declared in the `/understand` foundation's verification-kinds reference: five types — validation, testing, reviewing, auditing, evaluating — across two orthogonal axes, verdict mode (deterministic / agentic) and purpose (conformance / correctness). Three types back the tag an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing.

## Rationale

This product adopts the marketplace verification taxonomy rather than defining its own, so every node's evidence reads the same way across the spec tree and the two agentic types — auditing and reviewing — are themselves verified by graded eval cases. An audit verdict is produced in a verifier context isolated from the author context — the context that produced the work under audit — so the judgment stays free of the bias a context accumulates while producing the work it would otherwise grade. The isolation separates author from verifier, never one verifier from another: the author context dispatches the audit to a separate verifier context rather than grading its own work in place, and a verifier already free of author bias may compose further verification without reintroducing it.

## Product properties

1. Verification is the five marketplace types — validation, testing, reviewing, auditing, evaluating — across two axes, verdict mode and purpose. Three back the tag an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing.
2. Each path-bearing evidence link resolves to its target — a `[test]` link to an executable test, an `[eval]` link to an eval definition — and the `[audit]` tag is pathless.
3. An audit verdict is produced in a verifier context isolated from the author context — the context that produced the work under audit. The author context never grades its own work in place; it dispatches the audit to a separate verifier context. The isolation separates author from verifier, never one verifier from another, so a verifier already free of author bias may compose further verification.

## Verification

### Audit

- ALWAYS: an activity declares its type and purpose ([audit])
- NEVER: a type's verdict mode differs from the one its definition binds — the binding is fixed, not chosen per run ([audit])
- NEVER: a model judges the verdict of a deterministic type — it may run inside the process, but the verdict is the deterministic score ([audit])
- ALWAYS: an audit verdict is produced in a verifier context isolated from the author context that produced the work under audit — the isolation separates author from verifier, never one verifier from another ([audit])
- ALWAYS: the author context produces an audit verdict only by dispatching the audit to a separate verifier context — never by grading its own work in place ([audit])
- NEVER: the author context invokes an audit skill in place to produce a verdict — in-context invocation reintroduces the bias the dispatched verifier's isolated context removes ([audit])
- ALWAYS: a verifier already isolated from author bias may compose further verification — composition within a verifier context reintroduces no author bias ([audit])
- NEVER: the type set or the two verdict modes are extended — a new type amends the `/understand` foundation's verification-kinds reference and this decision ([audit])

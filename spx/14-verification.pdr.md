# Verification

This product adopts the verification taxonomy declared in the `/understand` foundation's verification-kinds reference: five types — validation, testing, reviewing, auditing, evaluating — across two orthogonal axes, verdict mode (deterministic / agentic) and purpose (conformance / correctness). Three types back the tag an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing.

## Rationale

This product adopts the marketplace verification taxonomy rather than defining its own, so every node's evidence reads the same way across the spec tree and the two agentic types — auditing and reviewing — are themselves verified by graded eval cases. An audit verdict is produced in an isolated agent context, reached only by dispatching the corresponding auditor agent, so the judgment stays free of the bias the main conversation accumulates while doing the work under audit. The rule binds the main conversation's entry point; a dispatched agent's own calls while it runs the audit are a separate concern.

Verification ownership spans all five types, not only the deterministic ones a CI gate re-runs. Passing tests and validation shows the changed code meets the checks that already exist; it does not show the design is coherent, the evidence sufficient, or a finding's defect class swept — the judgment only reviewing and auditing supply. An agent that defers those to an external reviewer lets the reviewer drive the design one finding per round; running them locally first forecloses that. Reading the changeset is the cheapest verification the agent has and the one that converges the design, so an agentic gate confirms an artifact already stabilized rather than discovering it. The scope split keeps per-iteration deterministic runs cheap while CI stays the full-repository regression net.

## Scope

**The changeset** is the files changed between the base ref and HEAD (`git diff <base>...<head>`) and the spec-tree node(s) that govern them — resolved by inverse navigation (a changed file → the tests that import it → the assertions linking those tests → the containing node), taking the lowest common ancestor when the change spans several nodes.

Verification runs over the changeset. The verdict mode determines whether CI widens that scope:

| Verdict mode  | Types                           | Local scope   | CI scope             |
| ------------- | ------------------------------- | ------------- | -------------------- |
| Deterministic | validation, testing, evaluating | the changeset | the whole repository |
| Agentic       | reviewing, auditing             | the changeset | the changeset        |

Deterministic types widen to the whole repository in CI because CI is the full-repository regression net. Agentic types do not widen — a review or audit inspects the change, not the repository — so local and CI inspect the same scope and the agent runs them locally first. Auditing's defect-class sweep reads the touched node(s)' other governed files, which is the changeset's node(s) at node granularity.

## Product properties

1. Verification is the five marketplace types — validation, testing, reviewing, auditing, evaluating — across two axes, verdict mode and purpose. Three back the tag an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing.
2. Each path-bearing evidence link resolves to its target — a `[test]` link to an executable test, an `[eval]` link to an eval definition — and the `[audit]` tag is pathless.
3. An audit verdict is produced in an isolated agent context, reached only by dispatching the corresponding auditor agent. The main conversation never invokes an audit skill in place to produce a verdict.
4. The agent owns all five verification types and runs each applicable one locally, over the changeset, before any external or CI review.
5. Deterministic verification (validation, testing, evaluating) runs over the changeset locally and over the whole repository in CI; agentic verification (reviewing, auditing) runs over the changeset both locally and in CI, per the Scope table.
6. Passing deterministic verification is the floor: it shows the changed code meets the deterministic checks that exist, establishes nothing about reviewing or auditing, and never on its own authorizes publishing.
7. A valid reviewing or auditing finding is a defect class: the agent fixes every same-class instance across the touched node(s), and a single-site fix stands only when a sweep shows no parallel instance.
8. An agentic verification gate confirms an artifact the agent has already stabilized by reading it; it is not the loop that discovers the design.

## Verification

### Audit

- ALWAYS: an activity declares its type and purpose ([audit])
- NEVER: a type's verdict mode differs from the one its definition binds — the binding is fixed, not chosen per run ([audit])
- NEVER: a model judges the verdict of a deterministic type — it may run inside the process, but the verdict is the deterministic score ([audit])
- ALWAYS: the main conversation produces an audit verdict only by dispatching the corresponding auditor agent — the auditor agent's isolated context is the surface that emits the verdict ([audit])
- NEVER: the main conversation invokes an audit skill in place to produce a verdict — direct in-context invocation reintroduces the bias the dispatched agent's isolated context removes ([audit])
- NEVER: the type set or the two verdict modes are extended — a new type amends the `/understand` foundation's verification-kinds reference and this decision ([audit])
- ALWAYS: the agent runs each applicable verification type locally over the changeset before any external or CI review — reviewing and auditing as well as validation, testing, and evaluating ([audit])
- ALWAYS: deterministic verification runs over the changeset locally and over the whole repository in CI; agentic verification runs over the changeset both locally and in CI ([audit])
- NEVER: passing deterministic verification on its own authorizes publishing — it establishes nothing about reviewing or auditing ([audit])
- ALWAYS: a valid reviewing or auditing finding is fixed as a defect class across the touched node(s), a single-site fix standing only when a sweep shows no parallel instance ([audit])
- ALWAYS: an agentic verification gate confirms an artifact already stabilized by the agent's reading, not the loop that discovers the design ([audit])

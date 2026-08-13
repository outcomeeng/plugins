# Verification

This product adopts the verification taxonomy declared in the inline `/understand` `<verification_model>`: five types — validate, test, review, audit, evaluate — across two orthogonal axes, verdict mode (deterministic / agentic) and purpose (conformance / correctness). Three types back the tag an assertion carries: `[test]` by test, `[eval]` by evaluate, `[audit]` by audit.

## Rationale

This product adopts the marketplace verification taxonomy rather than defining its own, so every node's evidence reads the same way across the spec tree and the two agentic types — audit and review — are themselves verified by graded eval cases. An audit verdict is produced in a verifier agent session isolated from the authoring agent session that produced the work under audit, so the judgment stays free of the bias an agent session accumulates while producing the work it would otherwise grade. The isolation separates author from verifier, never one verifier from another: the authoring agent session dispatches the audit to a separate verifier agent session rather than grading its own work in place, and a verifier already free of author bias may compose further verification without reintroducing it.

Verification ownership spans all five types, not only the deterministic ones a CI gate re-runs. Passing tests and validation shows the changed code meets the checks that already exist; it does not show the design is coherent, the evidence sufficient, or a finding's defect class swept — the judgment only review and audit supply. An agent that defers those to an external reviewer lets the reviewer drive the design one finding per round; running them locally first forecloses that. Reading the changeset is the cheapest verification the agent has and the one that converges the design, so an agentic gate confirms an artifact already stabilized rather than discovering it. The scope split keeps per-iteration deterministic runs cheap while CI stays the full-repository regression net.

## Scope

**The changeset** is the files changed between the base ref and HEAD (`git diff <base>...<head>`) and the spec-tree node(s) that govern them. When changed files span several nodes, their lowest common ancestor governs the combined verification scope.

Verification runs over the changeset. The verdict mode determines whether CI widens that scope:

| Verdict mode  | Types                    | Local scope   | CI scope             |
| ------------- | ------------------------ | ------------- | -------------------- |
| Deterministic | validate, test, evaluate | the changeset | the whole repository |
| Agentic       | review, audit            | the changeset | the changeset        |

Deterministic types widen to the whole repository in CI because CI is the full-repository regression net. Agentic types do not widen — a review or audit inspects the change, not the repository — so local and CI inspect the same scope and the agent runs them locally first. Audit's defect-class sweep reads the touched node(s)' other governed files, which is the changeset's node(s) at node granularity.

## Product properties

1. Verification is the five marketplace types — validate, test, review, audit, evaluate — across two axes, verdict mode and purpose. Three back the tag an assertion carries: `[test]` by test, `[eval]` by evaluate, `[audit]` by audit.
2. Each path-bearing evidence link resolves to its target — a `[test]` link to an executable test, an `[eval]` link to an eval definition — and the `[audit]` tag is pathless.
3. An audit verdict is produced in a verifier agent session isolated from the authoring agent session that produced the work under audit. The authoring agent session never grades its own work in place; it dispatches the audit to a separate verifier agent session. The isolation separates author from verifier, never one verifier from another, so a verifier already free of author bias may compose further verification.
4. The agent owns all five verification types and runs each applicable one locally, over the changeset, before any external or CI review.
5. Deterministic verification (validate, test, evaluate) runs over the changeset locally and over the whole repository in CI; agentic verification (review, audit) runs over the changeset both locally and in CI, per the Scope table.
6. Passing deterministic verification is the floor: it shows the changed code meets the deterministic checks that exist, establishes nothing about review or audit, and never on its own authorizes publishing.
7. A valid review or audit finding is a defect class: the agent fixes every same-class instance across the touched node(s), and a single-site fix stands only when a sweep shows no parallel instance.
8. Changes may remain uncommitted while the authoring agent session works on them. Before another agent session or human is expected or asked to read an exact version for collaboration or reusable verification, the current version is committed with verification state `passing`, `failing`, or `not-run`; after any further change, the new version is committed before another such reading. An explicit advisory audit or review may inspect modified or untracked work, but its verdict is not reusable gate evidence. Without repository-write authorization, a reading that requires a committed subject waits.
9. An agentic verification gate receives an exact committed changeset after applicable deterministic verification passes on that subject; any later change invalidates that verdict.
10. The authoring agent session brings the deterministic types (validate, test, evaluate) to passing on the changeset before it dispatches an agentic type (review, audit); an agentic verification run reads and judges the already-passing changeset and never re-runs deterministic verification. Each deterministic check runs to passing once on the changeset, not once per verifier — repeating it during every audit and review only multiplies cost. CI re-runs all verification over the whole repository, so a deterministic regression the local changeset run missed is still caught.

## Verification

### Audit

- ALWAYS: an activity declares its type and purpose ([audit])
- NEVER: a type's verdict mode differs from the one its definition binds — the binding is fixed, not chosen per run ([audit])
- NEVER: a model judges the verdict of a deterministic type — it may run inside the process, but the verdict is the deterministic score ([audit])
- ALWAYS: an audit verdict is produced in a verifier agent session isolated from the authoring agent session that produced the work under audit — the isolation separates author from verifier, never one verifier from another ([audit])
- ALWAYS: the authoring agent session produces an audit verdict only by dispatching the audit to a separate verifier agent session — never by grading its own work in place ([audit])
- NEVER: the authoring agent session invokes an audit skill in place to produce a verdict — same-session invocation reintroduces the bias the isolated verifier agent session removes ([audit])
- ALWAYS: a verifier already isolated from author bias may compose further verification — composition within a verifier agent session reintroduces no author bias ([audit])
- NEVER: the type set or the two verdict modes are extended — a new type amends the inline `/understand` `<verification_model>` and this decision ([audit])
- ALWAYS: the agent runs each applicable verification type locally over the changeset before any external or CI review — review and audit as well as validate, test, and evaluate ([audit])
- ALWAYS: deterministic verification runs over the changeset locally and over the whole repository in CI; agentic verification runs over the changeset both locally and in CI ([audit])
- NEVER: passing deterministic verification on its own authorizes publishing — it establishes nothing about review or audit ([audit])
- ALWAYS: a valid review or audit finding is fixed as a defect class across the touched node(s), a single-site fix standing only when a sweep shows no parallel instance ([audit])
- ALWAYS: changes may remain uncommitted while the authoring agent session works on them; before another agent session or human reads an exact version for collaboration or reusable verification, commit the current version with verification state `passing`, `failing`, or `not-run`, and commit each later version before another such reading; an explicit advisory audit or review may inspect modified or untracked work but supplies no reusable gate evidence; without repository-write authorization, defer a reading that requires a committed subject ([audit])
- ALWAYS: an agentic verification gate receives an exact committed changeset after applicable deterministic verification passes on that subject, and any later change invalidates that verdict ([audit])
- ALWAYS: the authoring agent session brings deterministic verification (validate, test, evaluate) to passing on the changeset before dispatching an agentic verification (review, audit) ([audit])
- NEVER: an agentic verification run (review, audit) runs deterministic verification (validate, test, evaluate) — the authoring agent session passes it on the changeset before dispatch, and CI re-runs all verification over the whole repository; repeating it during each agentic verification only multiplies cost ([audit])

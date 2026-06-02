# Verification

This product adopts the verification taxonomy declared in the `/understanding` foundation reference `src/plugins/spec-tree/skills/understanding/references/verification-kinds.md`: five types — validation, testing, reviewing, auditing, evaluating — across two orthogonal axes, verdict mode (deterministic / agentic) and purpose (conformance / correctness). Three types back the evidence lanes an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing.

Grounding for this product:

- The agentic types, auditing and reviewing, are LLM-driven; their skills are themselves validated by evals in this repository through `outcomeeng_evals`.
- Each path-bearing evidence link resolves to its target: a `[test]` link to a pytest collectable, an `[eval]` link to an `eval.toml`. The `[audit]` lane is pathless.

## Verification

### Audit

- ALWAYS: an activity declares its type and purpose ([audit])
- NEVER: a type's verdict mode differs from the one its definition binds — the binding is fixed, not chosen per run ([audit])
- NEVER: a model judges the verdict of a deterministic type — it may run inside the process, but the verdict is the deterministic score ([audit])
- NEVER: the type set or the two verdict modes are extended — a new type amends `src/plugins/spec-tree/skills/understanding/references/verification-kinds.md` and this decision ([audit])

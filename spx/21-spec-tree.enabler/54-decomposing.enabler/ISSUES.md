# ISSUES — Decomposing

Known issues and deferred decisions for `/decompose`. Coordination note: verify each entry against the
specs, decisions, and current intent before acting on it.

## Post-mutation validation has no command-backed gate

The skill writes and redistributes durable Spec Tree structure, then closes through a checklist without
running deterministic validation. A future `/decompose` change must add explicit pass/fail gates using
the product's author and verify commands, including `spx validation markdown` and
`spx spec status --format json`, before reporting a composed tree as successful.

**Trigger to revisit:** the `/decompose` implementation workflow is next changed. **Resolution shape:**
run the deterministic commands after mutation, stop on either nonzero result, and make their passing
results part of the skill's success contract.

## Index-ordering self-sufficiency carries `[audit]` evidence; the runtime-behavior `[eval]` is deferred

The ordering-model assertions added under `### Compliance` — the context-loading consequence of an
index, the disposition checkpoint, and the existing-sibling-not-a-precedent rule — are `[audit]`
evidence, verified by reading the skill body. They prove the skill *carries* the semantics. They do
not exercise the *runtime behavior*: an agent that reads `/decompose`, sees an existing `21-*` sibling,
proposes a new sibling, and rejects choosing the next sparse slot (e.g. `32`) unless it has proven a
real predecessor/successor edge. That behavior is the `[eval]` subject per `spx/15-spec-coverage.adr.md`
(LLM-driven skill behavior with a structured verdict), and this node has no `evals/` infrastructure yet.

**Trigger to revisit:** the eval harness is wired for a `/decompose` ordering case, or a regression
shows an agent re-taking the next sparse slot. **Resolution shape:** add an `evals/ordering-disposition/`
directory (eval.toml + cases.jsonl + prompt.md) whose case presents an existing lower-index sibling and
scores the agent's rejection of an unproven higher-index slot; once it lands, the context-loading-
consequence and existing-sibling assertions can carry `[eval]` evidence alongside `[audit]`.

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

# Diagnostics

PROVIDES a portable environment-diagnostics capability — the `diagnose` skill — that runs the deterministic `spx diagnose` pipeline with a plugin-shipped manifest and reports the resulting per-check verdicts with remediation judgment
SO THAT a user or agent working any spec-tree product
CAN self-diagnose a misconfigured environment without recalling and typing the underlying interrogation by hand

## Assertions

### Conformance

- On every shipped target, the plugin-shipped diagnose manifest carries the product's source-of-truth spx-version floor, the outcomeeng marketplace identity, and the selected check set, and embeds no expected or required plugin set — marketplace-install diagnosis derives expected plugin state from the checkout's per-runtime project declarations, per `spx/12-marketplace-state.adr.md` ([test](tests/test_manifest.conformance.l1.py))

### Compliance

- ALWAYS: the shipped diagnose skill locates and runs `spx diagnose` with the plugin-shipped manifest, relays its deterministic report verbatim, and adds remediation judgment only from the report's non-healthy verdicts ([eval](evals/diagnostic-remediation/eval.toml))
- ALWAYS: the shipped skill reasons only about surfaces the runtime exposes — the `spx` CLI, harness environment variables, worktree/session state, and install state — through `spx diagnose`, degrading a check to not-applicable where its surface is absent rather than misclassifying, and names no product-internal spec-tree node address ([audit])
- ALWAYS: each check is an independent named diagnostic carrying its own verdict and remediation; a new surface is added as a new check in `spx diagnose`, and a new judgment of a surface an existing check already reads extends that check's verdict set, neither rewriting unrelated checks ([audit])
- NEVER: the shipped skill carries check classification or overall-fold logic in its own body — deterministic diagnosis lives in `spx diagnose` per the node decision ([audit])

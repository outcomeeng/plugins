---
id: 01a0ebba-5f6a-71a9-ae8b-72f51b9b5926
malleability: spec
---

# Diagnostics

PROVIDES a portable environment-diagnostics capability — the `diagnose` skill — that runs the deterministic `spx diagnose` pipeline with a plugin-shipped manifest and reports the resulting per-check verdicts with remediation judgment
SO THAT a user or agent working any product-tree product
CAN self-diagnose a misconfigured environment without recalling and typing the underlying interrogation by hand

## Assertions

### Test.Compliance: marketplace selection

- marketplace-selection: ALWAYS: marketplace-install diagnosis derives expected selection from Claude Code's inventory recorded for the invocation checkout at project or local scope and raw selected-home Codex plugin declarations, including disabled and uncached entries, bounded by the corresponding committed marketplace catalog.
- activation-independent: NEVER: trusted-product activation or cache presence changes the expected Codex home-wide selection; native inspection executes outside trusted product configuration discovery.

### Test.Conformance: manifest

- [manifest-contents](tests/test_manifest.conformance.l1.py): On every shipped target, the plugin-shipped diagnose manifest carries the product's source-of-truth spx-version floor, the outcomeeng marketplace identity, and the selected check set, and embeds no expected or required plugin set

### Evaluate: [diagnostic-remediation](evals/diagnostic-remediation/eval.toml)

The shipped `diagnose` skill locates and runs `spx diagnose` with the plugin-shipped manifest, relays its deterministic report verbatim, and adds remediation judgment only from the report's non-healthy verdicts, one remediation item per non-healthy check naming that check, its verdict and its bucket as the item's severity, or, when `spx diagnose` fails to start and yields no report, one remediation item that names the startup failure as its subject, concern `spx-diagnose-startup`, with its action and no severity; the eval hands the skill the captured result of that run and compares the relayed report or the startup failure, and each remediation item, with the row's expectation.

| Case                           | `spx diagnose` result                                                                                                                                          | Relayed report or startup failure                                                                                         | Remediation                                                                                                                                                            |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| healthy-verbatim-report        | exit 0, overall `healthy`: `session-environment` reads `not-applicable` and `spx-reachability` reads `reachable`                                               | the report verbatim, overall `healthy`                                                                                    | none                                                                                                                                                                   |
| degraded-multiple-remediations | exit 0, overall `degraded`: `session-store` reads `orphaned-claims` and `spx-reachability` reads `below-floor`, each in bucket `degraded` with its remediation | the report verbatim, overall `degraded`                                                                                   | one item for `session-store` with verdict `orphaned-claims` and severity `degraded`, and one for `spx-reachability` with verdict `below-floor` and severity `degraded` |
| broken-cli-missing             | exit 127, empty stdout, stderr `zsh: command not found: spx`                                                                                                   | a startup failure carrying exit 127, the empty stdout and the stderr verbatim, and no relayed report of overall `healthy` | one item with concern `spx-diagnose-startup`, an action and no severity                                                                                                |

### Audit: harness surfaces and checks

- harness-surfaces: ALWAYS: the shipped skill reasons only about surfaces the agent harness exposes — the `spx` CLI, harness environment variables, worktree/session state, and install state — through `spx diagnose`, degrading a check to not-applicable where its surface is absent rather than misclassifying, and names no product-internal product-tree node address
- independent-checks: ALWAYS: each check is an independent named diagnostic carrying its own verdict and remediation; a new surface is added as a new check in `spx diagnose`, and a new judgment of a surface an existing check already reads extends that check's verdict set, neither rewriting unrelated checks
- no-fold-logic: NEVER: the shipped skill carries check classification or overall-fold logic in its own body — deterministic diagnosis lives in `spx diagnose` per the node decision

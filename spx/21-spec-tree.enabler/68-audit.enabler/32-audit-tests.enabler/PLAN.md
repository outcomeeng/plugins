# Plan - Audit Tests

Coordination note; not spec truth.

## Refresh producer-coupled eval run evidence

The `full-chain-ownership` and `full-chain-ownership-codex` eval suites embed
the producer skill `audit-tests` (the `src/plugins` and `dist/codex` variants)
verbatim in their `prompt.md`. A verdict-format wording change to that producer
— removing the JSON-consumer fiction and requiring a single JSON verdict —
re-materialized the prompts, so the committed `history.jsonl` rows predate the
current prompt content and no longer score the `[eval]`-backed assertion against
what the evals now embed.

Deferred by operator decision to keep the change scoped to the skill, spec,
agent, and prompt edits; the audit skill's verdict behavior is unchanged, only
the recorded run evidence is stale.

Next step: run
`just eval-node spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler`
at the default budget, confirm each suite passes its threshold, and commit the
fresh `history.jsonl` rows so the eval-evidence gate carries current run
evidence.

---
id: 01a11e45-4038-7647-bc58-31aac94f74c0
malleability: spec
---

# Audit Assertions

PROVIDES the isolated Agentic verdict on each `[audit]` assertion of one node's spec, judged against the subject the assertion names and recorded through `spx verification run`
SO THAT an Executor, a merge gate and a status claim
CAN read an `[audit]` result from a sealed run

## Assertions

- ALWAYS: `/audit-assertions` judges every `[audit:{rule-slug}]` and pathless `[audit]` assertion of the target spec against the subject that assertion names, and judges no assertion that carries another tag.
- ALWAYS: `/audit-assertions` starts one `spx verification run` before judging, records one scope unit per `[audit]` assertion keyed by its rule slug — a pathless `[audit]` assertion by its ordinal in the spec — with every finding on its unit, seals the run, and returns the run token with the rendered projection.
- NEVER: `/audit-assertions` judges how an assertion is declared or selected; declaration form and tag fit belong to the spec audit.
- ALWAYS: `assertion-auditor` passes the raw target spec path and a fixed run-driver identity to its skill, starts without the caller's authoring history, and relays the run token and the rendered projection unchanged, or the complete blocked diagnostic.

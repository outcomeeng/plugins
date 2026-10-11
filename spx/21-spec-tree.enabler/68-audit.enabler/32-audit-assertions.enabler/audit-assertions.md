---
id: 01a1281a-5c35-7339-ac52-207f93675c4c
malleability: spec
---

# Audit Assertions

PROVIDES the isolated Agentic verdict on each `[audit]` assertion of one node's spec, judged against the subject the assertion names and recorded through `spx verification run`
SO THAT an Executor, a merge gate and a status claim
CAN read an `[audit]` result from a sealed run

## Assertions

- ALWAYS: `/audit-assertions` judges every `[audit:{rule-slug}]` and pathless `[audit]` assertion of the target spec against the subject that assertion names, and judges no assertion that carries another tag
- ALWAYS: `/audit-assertions` starts one `spx verification run` before judging, records one scope unit per `[audit]` assertion keyed by its rule slug — a pathless `[audit]` assertion by its ordinal in the spec — with every finding on its unit, seals the run, and returns the run token with the rendered projection
- NEVER: `/audit-assertions` judges how an assertion is declared or selected; declaration form and tag fit belong to the spec audit
- ALWAYS: `assertion-auditor` passes the raw target spec path and a fixed run-driver identity to its skill, starts without the caller's authoring history, and relays the run token and the rendered projection unchanged, or the complete blocked diagnostic
- ALWAYS: `/audit-assertions` rejects only on touched text under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), returns each other finding as `filed`, and approves when no finding on touched text exists
- ALWAYS: `/audit-assertions` records each scope unit with audit class `spec` and audit kind `spec`, the audited node spec path as the unit subject, and the assertion's designator — its rule slug, or its ordinal when pathless — in the unit key and in the message of every finding on that unit
- Given the scope payload shape that `/audit-assertions` states, when its class and kind are checked against the pinned published SPX floor, then the floor accepts that class and kind for a node spec subject
- Given the scope payload shape that `/audit-assertions` states, when a run records a unit of that shape and a finding on that unit through the pinned published SPX CLI and finishes, then the CLI accepts every payload, seals the run, and returns the unit key and the terminal status the finding derives
- Given a node spec with an `[audit]` assertion, when a launched `spec-tree:assertion-auditor` audits it under the pinned published SPX floor, then the run seals with terminal status `approved` or `rejected`

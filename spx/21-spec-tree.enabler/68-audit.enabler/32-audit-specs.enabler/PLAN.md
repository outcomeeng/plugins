# Plan - Audit Specs

Coordination note; not spec truth.

## Refresh producer-coupled eval run evidence

The `structure` eval suite embeds the producer skill
`src/plugins/spec-tree/skills/audit-specs/SKILL.md` verbatim in its `prompt.md`.
A verdict-format wording change to that producer — removing the JSON-consumer
fiction and requiring a single JSON verdict — re-materialized the prompt, so the
committed `history.jsonl` rows predate the current prompt content.

This node is listed in `spx/EXCLUDE`: its `voice`, `tag-validity`, and
`prose-coupling` `[eval]` assertions are declared but not yet built, so the node
is already in a Specified-incomplete state. Refreshing the `structure` run
evidence is deferred by operator decision alongside that pending build-out.

Next step: when the node's eval build-out resumes, run
`just eval-node spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler`
at the default budget and commit the fresh `history.jsonl` rows, and author the
declared-but-missing `voice`, `tag-validity`, and `prose-coupling` eval suites.

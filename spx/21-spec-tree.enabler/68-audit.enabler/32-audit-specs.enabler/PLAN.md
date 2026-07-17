# Plan - Audit Specs

Coordination note; not spec truth.

## Build out the declared eval suites and refresh run evidence

This node is listed in `spx/EXCLUDE`: its `voice`, `tag-validity`, and
`prose-coupling` `[eval]` assertions are declared but not built, so the node is
Specified-incomplete.

The `structure` eval suite embeds the producer skill
`src/plugins/spec-tree/skills/audit-specs/SKILL.md` verbatim in its `prompt.md`,
so every edit to that producer re-materializes the prompt and leaves the
committed `history.jsonl` rows scoring prompt content the suite no longer
carries.

Do both in one pass, after the producer stops moving: the verification-run
migration in `spx/21-spec-tree.enabler/68-audit.enabler/PLAN.md` rewrites this
producer's verdict contract, so suites authored and run evidence recorded before
it lands are paid for again.

Next step, once that migration lands: author the declared `voice`,
`tag-validity`, and `prose-coupling` eval suites, run
`just eval-node spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler`
at the default budget, commit the fresh `history.jsonl` rows, and remove this
node's `spx/EXCLUDE` entry once the suites pass.

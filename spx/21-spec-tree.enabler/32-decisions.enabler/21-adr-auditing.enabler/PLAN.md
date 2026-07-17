# Plan - ADR Auditing

Coordination note; not spec truth.

## Refresh producer-coupled eval run evidence

The `structure`, `tag-validity`, and `voice` eval suites embed the producer
skill `src/plugins/spec-tree/skills/audit-adr/SKILL.md` verbatim in their
`prompt.md`, so every edit to that producer re-materializes the prompts and
leaves the committed `history.jsonl` rows scoring prompt content the suites no
longer carry.

Refresh once, after the producer stops moving: the verification-run migration in
`spx/21-spec-tree.enabler/68-audit.enabler/PLAN.md` rewrites this producer's
verdict contract, so run evidence recorded before it lands is paid for again.

Next step, once that migration lands: run
`just eval-node spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler`
at the default budget, confirm each suite passes its threshold, and commit the
fresh `history.jsonl` rows.

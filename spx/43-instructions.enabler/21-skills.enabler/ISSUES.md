# Issues: Skill Authoring

Actionable findings from the post-merge skill audit of PR 458 at
`f5aa313016964a10854117e026ec4c3529106490`.

## Split router authority by workflow needs

`src/plugins/instructions/skills/create-skill/SKILL.md:5` grants `Bash`, `Write`,
`WebFetch`, and `WebSearch` to every route. Read-only audit and pattern-explanation
routes inherit mutation and network capabilities they do not use.

Required handling: narrow the router's top-level `allowed-tools` surface or split
routes whose authority requirements differ. Preserve the tools required by creation
and improvement workflows without granting them to read-only routes.

Source: skill-auditor finding `f-003`, rule `overbroad_allowed_tools`, severity
`WARNING`.

## Reconcile the auditor Bash capability contract

`src/plugins/instructions/skills/create-skill/templates/auditor-skill.md:5` now uses
`allowed-tools: Read, Grep, Glob, Skill`. The post-merge audit requires `Bash` for
auditor command-based verification, while an earlier audit rejected bare `Bash` as
overbroad. `/skill-standards`'s command-capability rules also require command-specific
`Bash(<command>:*)` grants. A generic auditor template cannot select those commands
without knowing the generated auditor's workflow.

Required handling: decide whether every auditor requires `Bash`, define how a generic
template expresses least-privilege command grants, and align `/skill-standards`,
`/audit-skill`, and the auditor template so the same surface cannot be rejected both
for granting and omitting bare `Bash`.

Source: skill-auditor finding `f-004`, rule `read_only_audit_capabilities`, severity
`REJECT`, reconciled with the earlier `overbroad_allowed_tools` rejection.

## Revalidate after exercise-driven edits

`src/plugins/instructions/skills/create-skill/workflows/create-new-skill.md:79`
allows the representative exercise to trigger iterative edits after deterministic
checks and the skill audit have already completed. The final bundle can therefore
differ from the bundle those gates evaluated.

Required handling: run the representative exercise before final validation, or loop
every exercise-driven edit back through deterministic checks and the complete-bundle
skill audit before publication.

Source: PR 458 review comment `3610850053`, classified as `DEBT` in the `evidence`
category after merge.

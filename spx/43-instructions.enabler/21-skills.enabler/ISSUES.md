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

## `/audit-skill` declares no target argument and no no-target edge case

`src/plugins/instructions/skills/audit-subagent/SKILL.md` declares
`arguments: configured_agent_path` and stops with `REJECTED` naming the missing
argument when that path is empty. Its sibling
`src/plugins/instructions/skills/audit-skill/SKILL.md` declares no `arguments`,
no `argument-hint`, and no `$ARGUMENTS`, and carries no matching edge case for a
dispatch that names no target.

The asymmetry has two effects. A direct `/audit-skill` invocation resolves its
target from surrounding conversation rather than a declared contract, which
`/skill-standards` `<skill_organization>` requires to stay independently
invocable. And a malformed dispatch that supplies no path has no defined stop,
so the audit proceeds against whatever the context suggests.

Required handling: declare the argument surface `audit-skill` actually takes —
the changed skill-surface paths plus governing nodes and verification state —
and add the no-target edge case its sibling already states. `/skill-standards`
`references/command-capabilities.md` carries both candidate forms: `arguments`
with a YAML name list for stable tokens, whose worked example is
`audit-subagent`'s own `configured_agent_path`, and `$ARGUMENTS` for whole-string
capture where multi-word intent must survive. Either choice also owes the
`argument-hint` the reference requires of every skill that takes arguments.

Source: `instructions:skill-auditor` findings `f-007` and `f-010`, severity
`WARNING`, on the changeset merged as PR 488.

# Plan: realize the subagent triad

Governing declarations: `spx/43-instructions.enabler/21-subagents.enabler/subagents.md`
and `spx/14-skill-naming.pdr.md`.

The node declares three peers. Two ship: `/create-subagent` and `/audit-subagent`.
`/subagent-standards` is declared and not yet built, so the node's first two assertions
lead their implementation.

## Build `/subagent-standards` and empty both rulebooks

`src/plugins/instructions/skills/audit-subagent/SKILL.md` carries an
`<evaluation_areas>` and `<anti_patterns>` rulebook that restates
`/agent-prompt-standards`, because the auditor has no canonical-rules owner to load. The
same defect class sits in `src/plugins/instructions/skills/audit-skill/SKILL.md`
against `/skill-standards`;
`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` property 7
requires both to be swept together, so fixing one alone is an invalid single-site fix.

Worklist:

1. Author `/subagent-standards` as a reference skill owning the canonical subagent
   rules — configuration fields, tool grants, model selection, context isolation,
   invocation contract — migrated out of `/create-subagent`'s overview and references
   and out of the embedded rulebooks in both auditors.
2. Strip `<evaluation_areas>` and `<anti_patterns>` from both `/audit-subagent` and
   `/audit-skill`; each loads its standards skill and enforces without restating.
3. Regenerate both runtime trees, run the focused skill and documentation checks,
   dispatch `instructions:skill-auditor` over every changed skill surface, then run the
   changeset review.

The consolidation entries in
`spx/43-instructions.enabler/21-skills.enabler/ISSUES.md` — the `/create-subagent`
bundle duplication and the four deferred `WARNING` findings — resolve inside this work
rather than separately: extracting the canonical rules is that consolidation under a
governing principle.

## Establish evidence for the declared assertions

The node's assertions carry no verification tag. `/verify` selects each one's type.
`spx/15-spec-coverage.adr.md` routes LLM-driven skill behavior that emits a structured
verdict to `[eval]`, and `/audit-subagent` emits exactly such a verdict, so the
per-invocation-scope and read-only assertions are eval candidates rather than audit
ones. `spx/43-instructions.enabler/ISSUES.md` entry 4 records the matching gap for
`/audit-skill`; both auditors need the instructions plugin's first eval suite, so
establish them together.

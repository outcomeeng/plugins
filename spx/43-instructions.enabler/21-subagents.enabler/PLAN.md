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

## Carry the model-reproducibility rule into `/subagent-standards`

`/subagent-standards` owns model selection, so the canonical rule belongs in it:
a subagent that produces a verification verdict never inherits its model from the
invoking context, because a verdict a later invocation cannot reproduce is not
evidence.

Its `[test]` evidence follows the structural-constraint shape
`spx/15-validation.enabler/32-hook-safety.enabler` already uses — a source-owned
validator exercised against violating cases, never a scan asserting this
repository's own files comply, which would be the second declaration
`spx/12-shipped-scripting.adr.md` forbids. The validator needs two contracts
`outcomeeng/distribution/agents.py` does not yet expose: a predicate deciding
which agents produce a verification verdict, and the violation check itself.
`INHERIT_MODEL_VALUE` and `iter_agent_files` are already there.

Build the source contract before the test, per `/test-python`'s split mode.

## Build the declared eval suite

`/verify` routed the per-invocation-scope assertion to `[eval]`: `/audit-subagent`
is an LLM-driven producer emitting a structured verdict whose `target` a grader
scores, which `spx/15-spec-coverage.adr.md` sends to the eval lane. The suite at
`evals/invocation-scope/` is declared and not built, so the node is
Specified-incomplete and carries an `spx/EXCLUDE` entry until the suite passes.

`spx/43-instructions.enabler/ISSUES.md` entry 4 records the matching gap for
`/audit-skill`. Both auditors need the instructions plugin's first eval suite, so
build them together and remove the `spx/EXCLUDE` entry once they pass.

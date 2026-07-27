# Issues: Prose Plugin

## `audit-internal-docs` emits no structured verdict, so its behavior is not gradeable

`audit-internal-docs` produces a prose flag list and states no overall determination. Every other auditor in the marketplace emits a machine-readable verdict: `audit-python-code` returns `overall`, `rows[]`, and `findings[]` carrying `file`, `line`, `rule`, `severity`, `observed`, and `expected`; `audit-implementation` streams the same shape into the run journal through `spx verification run` and treats the rendered projection's `terminalStatus` as authoritative. `spx/21-spec-tree.enabler/16-verification.enabler` records that every agentic verification surface drives that one projection, and `spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md` names a prompt-only simulation of a producer's policy as invalid evidence for that producer.

The consequence is that `[eval]` evidence cannot couple to this skill. An eval must grade a structured verdict the producer emits; with none available, a suite has to impose its own schema in the prompt template and grade that instead — which measures the prompt author's schema, not the skill. Routing evals built this way were removed rather than shipped as evidence that looks stronger than it is.

**Resolution shape**: give `audit-internal-docs` a verdict contract in the `audit-python-code` shape — a binary overall determination plus structured findings — and decide whether it is a leaf concern returning results to a run driver or an agentic verification surface that records its own run. Then author `[eval]` evidence that grades that contract, and reconcile the `[audit]` assertions in `spx/43-prose.enabler/prose.md` against it. `audit-prose` carries the same gap and moves with it.

This is larger than a routing-boundary change: it redesigns the skill's output contract, touches the sibling `audit-prose`, and changes what evidence class the node's assertions carry.

## Reference-skill `<success_criteria>` prove a downstream document, not the catalog

`internal-doc-standards` and `prose-standards` both state `<success_criteria>` as properties of a document that applied the catalog — opening sentence substantive, acronyms reused twice, em dashes under three. Each `<objective>` names the catalog itself as the output, so neither file's criteria prove the artifact the skill produces. Nothing checks that every rule in `<inherited_rules>`, `<overrides>`, and `<additional_rules>` carries a worked Avoid/Prefer pair, which is the property that would establish the catalog is sound.

Both reference skills carry the identical shape, so the fix belongs to the pair rather than to one file: correcting `internal-doc-standards` alone would leave the two siblings inconsistent for readers who compose them together. The resolution is one criterion per catalog verifying the catalog's own completeness, kept alongside the document-facing checklist that consumers rely on.

## Skill-delegation `Skill` allowed-tools gap — PR3 (prose half) (CLOSED)

**Closed (branch `fix/skill-delegation-allowed-tools-develop-prose`, shipped with the develop half).**
`Skill` appended to `allowed-tools` on all three delegating skills: `audit-prose` and
`audit-internal-docs` (now `Read, Glob, Grep, Bash, Skill`, read-only — no `Write`/`Edit`) and
`write-internal-docs` (now `Read, Edit, Write, Glob, Grep, Skill`). The `instructions:skill-auditor` gate
ran on every changed SKILL.md and confirmed the appends clean; it also surfaced one touched-file
worth-fixing item resolved in this PR — `write-internal-docs` used the forbidden corporate-metaphor
phrase "earn their keep" (reworded to "are worth the visual weight"). `prose-standards` (reference)
and `write-prose` (empty `allowed-tools`, unrestricted) were correctly NOT gaps.

A skill whose body invokes another skill needs `Skill` in `allowed-tools`, or the delegation requires
per-call approval. The marketplace-wide `require_skill` → `Skill` sweep closed spec-tree/python/rust in
PR #279; the cross-plugin context, the detection heuristic, and the develop half of this PR live in
`spx/43-instructions.enabler/ISSUES.md` §2.

**The 3 prose skills needing `Skill` appended to `allowed-tools`** (each carries the
`{!% require_skill … %!}` macro):

- `audit-prose` (`allowed-tools: Read, Glob, Grep, Bash`) — read-only audit skill: append `Skill`
  only, never `Write`/`Edit`.
- `audit-internal-docs` (`allowed-tools: Read, Glob, Grep, Bash`) — same, read-only.
- `write-internal-docs` (`allowed-tools: Read, Edit, Write, Glob, Grep`) — append `Skill`.

`prose-standards` is a reference skill ("invoke X **instead of** me") and is NOT a gap; `write-prose`
has an **empty** `allowed-tools` (unrestricted) and needs no change.

**Packaging:** ships in ONE PR together with the develop half (`audit-commands`, `audit-skill`,
`audit-subagent` — see `spx/43-instructions.enabler/ISSUES.md` §2). Each plugin gets its own patch bump in
the same PR (PR #279 bundled three plugins this way).

**Procedure:** edit src → `just build-skills` → gate every changed SKILL.md with `instructions:skill-auditor`
(the changes-reviewer and CI `spec-tree-review` do not load skill standards; only the auditor catches
voice/structure/portability) → fix every must-fix the auditor surfaces on touched files → `just bump`
(prose + develop, each patch) → `/merge`. Expect the auditor to also flag pre-existing marketplace-wide
classes (verdict-path citation, `<quick_start>` on validators) that are out of scope and tracked in
`spx/43-instructions.enabler/ISSUES.md` §2.

Surfaced by PR #279 (the spec-tree/python/rust Skill-gap sweep).

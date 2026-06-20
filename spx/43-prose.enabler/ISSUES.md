# Issues: Prose Plugin

## Skill-delegation `Skill` allowed-tools gap — PR3 (prose half) (OPEN)

A skill whose body invokes another skill needs `Skill` in `allowed-tools`, or the delegation requires
per-call approval. The marketplace-wide `require_skill` → `Skill` sweep closed spec-tree/python/rust in
PR #279; the cross-plugin context, the detection heuristic, and the develop half of this PR live in
`spx/43-develop.enabler/ISSUES.md` §2.

**The 3 prose skills needing `Skill` appended to `allowed-tools`** (each carries the
`{!% require_skill … %!}` macro):

- `audit-prose` (`allowed-tools: Read, Glob, Grep, Bash`) — read-only audit skill: append `Skill`
  only, never `Write`/`Edit`.
- `audit-internal-docs` (`allowed-tools: Read, Glob, Grep, Bash`) — same, read-only.
- `write-internal-docs` (`allowed-tools: Read, Edit, Write, Glob, Grep`) — append `Skill`.

`prose-standards` is a reference skill ("invoke X **instead of** me") and is NOT a gap; `write-prose`
has an **empty** `allowed-tools` (unrestricted) and needs no change.

**Packaging:** ships in ONE PR together with the develop half (`audit-commands`, `audit-skills`,
`audit-subagents` — see `spx/43-develop.enabler/ISSUES.md` §2). Each plugin gets its own patch bump in
the same PR (PR #279 bundled three plugins this way).

**Procedure:** edit src → `just build-skills` → gate every changed SKILL.md with `develop:skill-auditor`
(the changes-reviewer and CI `spec-tree-review` do not load skill standards; only the auditor catches
voice/structure/portability) → fix every must-fix the auditor surfaces on touched files → `just bump`
(prose + develop, each patch) → `/merge`. Expect the auditor to also flag pre-existing marketplace-wide
classes (verdict-path citation, `<quick_start>` on validators) that are out of scope and tracked in
`spx/43-develop.enabler/ISSUES.md` §2.

Surfaced by PR #279 (the spec-tree/python/rust Skill-gap sweep).

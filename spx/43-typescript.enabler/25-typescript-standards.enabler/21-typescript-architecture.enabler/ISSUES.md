# Issues: typescript-architecture

Known defects for this node. Reconcile against current specs, decisions, and evidence
before acting — a note is a stale-prone input, not authority.

## `typescript-principles.md` does not follow the reference-file structure standard

`src/plugins/typescript/skills/architect-typescript/references/typescript-principles.md`
uses Markdown `#`/`##` headings throughout instead of the semantic XML sections
`instructions:skill-standards` requires, and at 144 lines it exceeds that skill's
100-line threshold for a contents list without carrying one.
`src/plugins/spec-tree/skills/merging-standards/references/merge-policy.md` is the
in-repository model: a hand-maintained `<contents>` block whose entry order matches the
file's section order.

Required: convert the six top-level headings to semantic XML sections and add a contents
list ordered to match.

Out of scope for the path-boundary changeset that surfaced it: that changeset's bounded
concern is scratch-path and repository-target enforcement, and it edited this file on one
line only. Restructuring the whole reference is a documentation-structure concern with its
own skill-auditor gate, so it carries no dependency on the boundary work and does not
block it.

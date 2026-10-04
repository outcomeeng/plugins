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

## The architecture standards restate the decision template

A standard begins by loading the matching `/understand` template when one exists, and no skill encodes the template's shape, because a restated shape drifts the moment the template advances. The prose plugin conforms. In this node's skills, `src/plugins/typescript/skills/architect-typescript/SKILL.md` restates the ADR section list inline (title and decision, Rationale, Invariants, Verification, in the list that starts at line 144), and `src/plugins/typescript/skills/typescript-architecture-standards/SKILL.md` carries the same shape.

**Settlement condition.** Each restated section list becomes a pointer that loads the decision template through the live `/understand` foundation, keeping only language-specific content rules: dependency-injection patterns, testability constraints and per-language verification routing. The Python and Rust pairs carry the same gap in `spx/43-python.enabler/25-python-standards.enabler/21-python-architecture.enabler/ISSUES.md` and `spx/43-rust.enabler/ISSUES.md`, and each plugin's changeset gates its skills with `instructions:skill-auditor`.

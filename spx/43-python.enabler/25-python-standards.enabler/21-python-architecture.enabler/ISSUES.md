# Issues: Python Architecture

## The `architect-python` references carry markdown headings instead of XML sections

`/skill-standards` `<xml_structure>` requires pure-XML structure with no markdown headings in a **SKILL.md body**; it does not extend that rule to bundled reference files. All three references under `src/plugins/python/skills/architect-python/references/` use `#`/`##`/`###` throughout:

- `architecture-patterns.md` (~466 lines)
- `testability-patterns.md` (~471 lines)
- `type-system-patterns.md` (~406 lines)

**Status against the standard.** The heading style violates no stated rule. The one stated requirement that does reach reference files — `/skill-standards` `<progressive_disclosure>`, "reference files over 100 lines need a table of contents at the top" — is satisfied: all three carry a `## Contents` section listing every top-level section.

**Evidence.** The skill audit raised the XML-section conversion in three consecutive runs against `src/plugins/python/skills/architect-python/references/`, each time at recommendation severity and each time naming the same three files. Recommendation severity is the auditor's own reading; no rule in `/skill-standards` makes the current form non-conformant.

**Why it is recorded rather than fixed.** Converting roughly 1,300 lines of nested prose, tables, and code blocks into semantic XML sections rewrites all three files end to end. The changeset that surfaced it edits 62 lines across those same files, so the conversion would be roughly twenty times the size of the substantive change it accompanies and would bury that change in a whole-file diff. [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) permits deferring a finding whose fix is a separate larger concern when the recorded reason names why it is large; the scale of the rewrite against the scale of the accompanying edit is that reason.

**Resolution shape.** Convert all three files in one dedicated changeset, choosing semantic tag names from the section content — `<dependency_injection>`, `<hexagonal_architecture>`, and so on — rather than transliterating heading text. Replace each `## Contents` block with a `<reference_index>` section in the same pass. Run the skill auditor over the `architect-python` skill afterward, since the same run that recommends this conversion also checks the result.

**Revisit condition.** Resolve when `architect-python` next needs a substantive content change to any of the three references, or when a skill audit escalates the finding above recommendation severity.

## The architecture standards restate the decision template

A standard begins by loading the matching `/understand` template when one exists, and no skill encodes the template's shape, because a restated shape drifts the moment the template advances. The prose plugin conforms. In this node's skills, `src/plugins/python/skills/python-architecture-standards/SKILL.md` and `src/plugins/python/skills/architect-python/SKILL.md` restate the ADR section list inline.

**Settlement condition.** Each restated section list becomes a pointer that loads the decision template through the live `/understand` foundation, keeping only language-specific content rules: dependency-injection patterns, testability constraints and per-language verification routing, with each plugin's changeset gating its skills with `instructions:skill-auditor`. The TypeScript and Rust pairs carry the same gap in `spx/43-typescript.enabler/25-typescript-standards.enabler/21-typescript-architecture.enabler/ISSUES.md` and `spx/43-rust.enabler/ISSUES.md`.

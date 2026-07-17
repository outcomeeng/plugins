# ISSUES - skills

Known issues for `spx/43-instructions.enabler/21-skills.enabler`.

## 1. Creator workflows diverge from current skill standards

The workflows under `src/plugins/instructions/skills/create-skills/workflows/` predate the current pure-XML, portability, objective-shape, and read-only audit contracts.

Required handling:

- Rewrite `audit-skill.md` and `create-new-skill.md` as pure XML workflow files without Markdown headings.
- Replace `~/.claude/skills/` and other runtime-specific authoring paths with source-owned or runtime-neutral paths.
- Require `<objective>` and `<success_criteria>` for every skill; evaluate router tags separately and treat `<quick_start>` as conditional by skill class.
- Reserve `<workflow>` for `SKILL.md` and `<process>` for files under `workflows/`.
- Replace the numeric audit score and unsolicited fix offer with the structured, read-only verdict contract from `/audit-skills`.
- Remove the required `## Before Implementation` Markdown section from generated skill guidance.
- Preserve the eager-foundation exception added by this changeset when replacing the legacy unconditional 500-line checks.

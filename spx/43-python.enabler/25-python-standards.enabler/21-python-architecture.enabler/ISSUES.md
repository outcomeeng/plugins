# Issues: Python Architecture

## The `architect-python` references carry markdown headings instead of XML sections

`/skill-standards` `<reference_file_guidance>` calls for pure-XML section tags in bundled reference files and treats markdown headings there as a recommendation rather than a violation — critical only in a `SKILL.md`. All three references under `src/plugins/python/skills/architect-python/references/` still use `#`/`##`/`###` throughout:

- `architecture-patterns.md` (~454 lines)
- `testability-patterns.md` (~459 lines)
- `type-system-patterns.md` (~392 lines)

**Evidence.** The skill audit raised this in three consecutive runs against `src/plugins/python/skills/architect-python/references/`, each time at recommendation severity and each time naming the same three files.

**Why it is recorded rather than fixed.** Converting roughly 1,300 lines of nested prose, tables, and code blocks into semantic XML sections is a rewrite of all three files, not an edit to the sections a changeset happens to touch. Doing it inside a changeset that edits one region of one file would replace a reviewable diff with a whole-file rewrite and hide the substantive change. The heading style also breaks nothing: these files are read as bundled references, and the standard permits the current form.

**Resolution shape.** Convert all three files in one dedicated changeset, choosing semantic tag names from the section content — `<dependency_injection>`, `<hexagonal_architecture>`, and so on — rather than transliterating heading text. Run the skill auditor over the `architect-python` skill afterward, since the same run that recommends this conversion also checks the result.

**Revisit condition.** Resolve when `architect-python` next needs a substantive content change to any of the three references, or when a skill audit escalates the finding above recommendation severity.

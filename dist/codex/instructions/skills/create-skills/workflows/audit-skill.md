<required_reading>
Read `/skill-standards` and `/agent-prompt-standards` before running this workflow. Check for `spx/local/skills.md` at the repository root and read it when present.
</required_reading>

<process>

<step name="identify_target">

Accept the skill path supplied by the operator. When no path is supplied, list the available skills and ask which one to audit. Resolve the target to its `SKILL.md` plus every cited file under `references/`, `workflows/`, `templates/`, and `scripts/`.

</step>

<step name="dispatch_audit">

Dispatch the configured `skill-auditor` with the repository path, every target skill-content path, governing node paths when known, and deterministic verification already run. The audit is read-only: never edit files, assign a numeric score, or ask the auditor to produce fixes.

The verdict must evaluate:

- YAML frontmatter and argument integration
- Required `<objective>` and `<success_criteria>` tags for every skill
- Additive router tags for router skills
- Pure XML body structure and closed tags
- Conditional tags appropriate to the skill type
- Progressive disclosure or the eager-foundation exception
- Command-capability security and bundled-file portability
- Prompt voice, constraint strength, conciseness, and operational effectiveness

</step>

<step name="present_verdict">

Present the auditor's complete JSON verdict unchanged, including its `overall` value (`APPROVED` or `REJECTED`) and every `keep-these-aspects`, `worth-improving`, and `must-fix` row with file and line locations. Never convert the verdict into a score or offer mutations as part of the audit workflow. A separate operator request to improve the skill returns to `/create-skills` for authoring after the read-only verdict is complete.

</step>

</process>

<audit_anti_patterns>

| Anti-pattern               | Defect                                                                            |
| -------------------------- | --------------------------------------------------------------------------------- |
| Skippable principles       | Essential principles live outside the eagerly loaded skill surface                |
| Monolithic optional detail | Conditional material is inlined without satisfying the eager-foundation exception |
| Hybrid structure           | Markdown headings appear in an XML-structured body                                |
| Missing required tags      | `<objective>` or `<success_criteria>` is absent                                   |
| Broken reference           | A cited bundled file is absent or reached through a nonportable path              |
| Score-based audit          | A numeric rating replaces actionable findings and an approval verdict             |
| Audit mutation             | The audit edits files or offers fixes inside its read-only workflow               |

</audit_anti_patterns>

<success_criteria>

- The target skill and every cited bundled file were included in the audit scope.
- The configured `skill-auditor` returned a terminal `APPROVED` or `REJECTED` verdict.
- Every rejection names a concrete file, line, governing standard, and required correction.
- The workflow performed no repository mutation and emitted no numeric score.

</success_criteria>

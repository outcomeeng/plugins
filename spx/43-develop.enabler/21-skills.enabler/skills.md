# Skills

PROVIDES the meta-skills that create, standardize, and audit SKILL.md files
SO THAT plugin authors
CAN produce skills that conform to the Agent Skills open standard and activate reliably at runtime

The skills-about-skills cluster is three peers with distinct roles:

- `/creating-skills` routes skill creation, editing, and improvement through typed workflows — builder, reference, validator, router.
- `/standardizing-skills` owns the canonical rules — frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence and bash constraints, validation, script testing. Loaded by the other two.
- `/auditing-skills` evaluates SKILL.md files against `/standardizing-skills` and `/standardizing-agent-prompts`, producing structured verdicts without modifying files.

## Assertions

### Compliance

- ALWAYS: `/standardizing-skills` owns every rule `/auditing-skills` enforces — standards and enforcement stay in one place so drift cannot open between them ([review])
- ALWAYS: `/creating-skills` and `/auditing-skills` load `/standardizing-skills` before doing any authoring or evaluation work — prevents memory-based assessment ([review])
- ALWAYS: `/auditing-skills` emits structured verdicts and performs no file modifications — audits inform decisions; they do not implement them ([review])
- NEVER: restate `/standardizing-skills` rules inside `/creating-skills` or `/auditing-skills` — a single source of truth prevents drift between standard and enforcer ([review])
- NEVER: add standards content to `/creating-skills/references/` — that directory carries workflow guidance; standards belong in `/standardizing-skills` ([review])

# Skills

PROVIDES the meta-skills that create, standardize, and audit SKILL.md files
SO THAT plugin authors
CAN produce skills that conform to the Agent Skills open standard and activate reliably at runtime

The skills-about-skills cluster is three peers with distinct roles:

- `/create-skills` routes skill creation, editing, and improvement through typed workflows — builder, reference, validator, router.
- `/skill-standards` owns the canonical rules — frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence and bash constraints, validation, script testing. Loaded by the other two.
- `/audit-skills` evaluates SKILL.md files against `/skill-standards` and `/agent-prompt-standards`, producing structured verdicts without modifying files.

## Assertions

### Compliance

- ALWAYS: `/skill-standards` owns every rule `/audit-skills` enforces — standards and enforcement stay in one place so drift cannot open between them ([review])
- ALWAYS: `/create-skills` and `/audit-skills` load `/skill-standards` before doing any authoring or evaluation work — prevents memory-based assessment ([review])
- ALWAYS: `/audit-skills` emits structured verdicts and performs no file modifications — audits inform decisions; they do not implement them ([review])
- ALWAYS: a skill governs its own behavior and remains independent of the agent, skill, or context that invokes it ([review])
- NEVER: a skill names, describes, detects, constrains, refuses, branches on, or otherwise depends on its invoker — context placement and dispatch policy belong to the invoking surface per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- NEVER: block model invocation of a skill an agent preloads with `disable-model-invocation` — it also blocks that preload and skill-to-skill loading ([review])
- NEVER: restate `/skill-standards` rules inside `/create-skills` or `/audit-skills` — a single source of truth prevents drift between standard and enforcer ([review])
- NEVER: add standards content to `/create-skills/references/` — that directory carries workflow guidance; standards belong in `/skill-standards` ([review])

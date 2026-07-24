# Skills

PROVIDES the meta-skills that create, standardize, and audit SKILL.md files
SO THAT plugin authors
CAN produce skills that conform to the Agent Skills open standard and activate reliably at runtime

The skills-about-skills cluster is three peers with distinct roles:

- `/create-skill` routes skill creation, editing, and improvement through typed workflows — builder, reference, validator, router.
- `/skill-standards` owns the canonical rules — frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence and bash constraints, validation, script testing. Loaded by the other two.
- `/audit-skill` evaluates SKILL.md files against `/skill-standards` and `/agent-prompt-standards`, producing structured verdicts without modifying files.

## Assertions

### Compliance

- ALWAYS: `/skill-standards` owns every rule `/audit-skill` enforces — standards and enforcement stay in one place so drift cannot open between them ([audit])
- ALWAYS: `/create-skill` and `/audit-skill` load `/skill-standards` before doing any authoring or evaluation work — prevents memory-based assessment ([audit])
- ALWAYS: `/audit-skill` emits structured verdicts and performs no file modifications — audits inform decisions; they do not implement them ([audit])
- ALWAYS: a skill governs its own behavior and remains independent of the agent, skill, or context that invokes it ([audit])
- ALWAYS: before proposing or applying a skill rename, `/create-skill` classifies every skill the repository requires reviewing by current name, skill type, governing naming form, proposed name or keep disposition, and reason; it reads declared methodology vocabulary and relevant file history before calling a name defective, and never infers a batch rename from a shared token, suffix, or grammatical number ([audit])
- NEVER: a skill names, describes, detects, constrains, refuses, branches on, or otherwise depends on its caller — context placement and dispatch policy belong to the caller ([audit])
- NEVER: block model invocation of a skill an agent preloads with `disable-model-invocation` — it also blocks that preload and skill-to-skill loading ([audit])
- NEVER: restate `/skill-standards` rules inside `/create-skill` or `/audit-skill` — a single source of truth prevents drift between standard and enforcer ([audit])
- NEVER: add standards content to `/create-skill/references/` — that directory carries workflow guidance; standards belong in `/skill-standards` ([audit])
- ALWAYS: when a foundation skill loads the same references on every invocation, `/skill-standards` requires one consolidated canonical eager payload and governs its total loaded size instead of applying the 500-line overview rule; conditional operational detail, templates, examples, and overlays remain separate ([audit])

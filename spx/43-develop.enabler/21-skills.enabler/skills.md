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
- ALWAYS: a skill an auditor agent preloads (an `audit-*` skill) carries a dispatch gate at the top of its body that halts a main-conversation invocation and directs it to dispatch the corresponding auditor agent — the agent's isolated context is where the audit runs, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- ALWAYS: an agent-loaded `audit-*` skill's description names its auditor agent as the entry point and directs dispatch rather than carrying a bare main-conversation self-activation directive ([review])
- NEVER: block main-conversation invocation of an agent-loaded `audit-*` skill with `disable-model-invocation` — it also blocks the auditor agent's preload and skill-to-skill loading, so the dispatch gate and description enforce the rule instead ([review])
- NEVER: restate `/skill-standards` rules inside `/create-skills` or `/audit-skills` — a single source of truth prevents drift between standard and enforcer ([review])
- NEVER: add standards content to `/create-skills/references/` — that directory carries workflow guidance; standards belong in `/skill-standards` ([review])

# Skills

PROVIDES the meta-skills that create, standardize, and audit SKILL.md files
SO THAT plugin authors
CAN produce skills that conform to the Agent Skills open standard and activate reliably at runtime

The skills-about-skills cluster is three peers with distinct roles:

- `/create-skill` routes skill creation, editing, improvement, and repair through typed workflows — builder, reference, validator, router — and returns a finished bundle ready for independent verification.
- `/skill-standards` owns the canonical rules and their rule catalog — frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence and bash constraints, validation, script testing. Loaded by the other two.
- `/audit-skill` judges the skill files a changeset changes against the `/skill-standards` and `/agent-prompt-standards` rule catalogs, recording a sealed verification run and modifying no subject or product file.

## Assertions

- ALWAYS: `/audit-skill` records one changeset-scoped verification run with one unit for each bundle file the changeset changes, keyed `instructions:skill:file:<path>`, keys each finding `<unit>:<rule-id>`, and returns `BLOCKED` when the changeset leaves the bundle unchanged or a governing standard is unreadable.
- ALWAYS: every rule identifier `/audit-skill` records names a rule in the `/skill-standards` or `/agent-prompt-standards` rule catalog, and no finding is recorded under an identifier outside those catalogs.

### Compliance

- ALWAYS: a composing skill names each static dependency — one `plugin:skill` name with no argument — through the shared `require_skill` directive, states a dependency that carries an argument or a run-time-resolved name as the owned `Use skill` sentence with that value in place, and declares skill-use capability through the optional `tool('use_skill')` frontmatter token, so every generated agent surface receives its native instruction and capability set ([audit])
- ALWAYS: `/create-skill` applies the `/skill-standards` and `/agent-prompt-standards` rule catalogs to the bundle it produces or improves and returns that bundle ready for independent verification ([audit])
- ALWAYS: `/create-skill` carries no route that dispatches a skill auditor or waits on an audit verdict, and it repairs a bundle from supplied findings through a repair workflow that repairs and exercises the bundle before validating it ([audit])
- ALWAYS: `/skill-standards` and `/agent-prompt-standards` each own one rule catalog that gives every rule one stable identifier and one severity, and the `/skill-standards` auditor skeleton keys each finding by its unit and its catalog rule identifier ([audit])
- ALWAYS: `/skill-standards`' auditor skeleton admits a sealed `spx verification run` projection as an auditor's verdict format, in which each finding's key names its catalog rule identifier ([audit])

- ALWAYS: skill-authoring and audit guidance forbids model and reasoning
  overrides in skill frontmatter; a skill retains its invoking agent session's
  configuration in every supported product, including when invoked by a
  configured subagent, per [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) ([audit])
- ALWAYS: `/skill-standards` owns every rule `/audit-skill` enforces — standards and enforcement stay in one place so drift cannot open between them ([audit])
- ALWAYS: `/create-skill` and `/audit-skill` load `/skill-standards` before doing any authoring or evaluation work — prevents memory-based assessment ([audit])
- ALWAYS: a skill governs its own behavior and remains independent of the agent, skill, or context that invokes it ([audit])
- ALWAYS: `/skill-standards` requires a workflow step writing outside the invocation checkout to obtain confirmation naming the absolute destination before that write, and `/audit-skill` flags an unconfirmed one as blocking — resolving a path establishes where it is, never permission to write there ([audit])
- NEVER: `/skill-standards` permits skill content that frames a permission prompt, sandbox refusal, or tool-layer decline as an obstacle and documents a route around it, and `/audit-skill` flags such content as blocking — a documented bypass turns one operator's approval into a standing one for every session that loads the skill ([audit])
- ALWAYS: before proposing or applying a skill rename, `/create-skill` classifies every skill the repository requires reviewing by current name, skill type, governing naming form, proposed name or keep disposition, and reason; it reads declared methodology vocabulary and relevant file history before calling a name defective, and never infers a batch rename from a shared token, suffix, or grammatical number ([audit])
- NEVER: a skill names, describes, detects, constrains, refuses, branches on, or otherwise depends on its caller — context placement and dispatch policy belong to the caller ([audit])
- NEVER: block model invocation of a skill an agent preloads with `disable-model-invocation` — it also blocks that preload and skill-to-skill loading ([audit])
- NEVER: restate `/skill-standards` rules inside `/create-skill` or `/audit-skill` — a single source of truth prevents drift between standard and enforcer ([audit])
- NEVER: add standards content to `/create-skill/references/` — that directory carries workflow guidance; standards belong in `/skill-standards` ([audit])
- ALWAYS: when a foundation skill loads the same references on every invocation, `/skill-standards` requires one consolidated canonical eager payload and governs its total loaded size instead of applying the 500-line overview rule; conditional operational detail, templates, examples, and overlays remain separate ([audit])
- ALWAYS: `/skill-standards` states the guard-block rule the generated router states — a block on a command holding one operation with every string written literally ends its family, a block on a command whose composition the parts cannot carry — a process substitution, a pipe between two operations other than a payload pipe, a background `&`, a subshell, or a list that mixes `&&` and `||` — ends it too, and a block on a compound command runs its parts again one at a time, in their original order, with every string written literally, a payload pipe never split ([audit])

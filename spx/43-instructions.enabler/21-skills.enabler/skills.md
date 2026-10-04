# Skills

PROVIDES the meta-skills that create, standardize, and audit SKILL.md files
SO THAT plugin authors
CAN produce skills that conform to the Agent Skills open standard and activate reliably at runtime

The skills-about-skills cluster is three peers with distinct roles:

- `/create-skill` routes skill creation, editing, and repair through typed workflows — builder, reference, validator, router — and returns each produced skill ready for independent verification.
- `/skill-standards` owns the canonical rules — frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence and bash constraints, validation, script testing — and the rule catalog that names each of those rules. Loaded by the other two.
- `/audit-skill` evaluates the skill files a changeset changes against `/skill-standards` and `/agent-prompt-standards`, recording a sealed verification run and modifying no subject or product file.

## Assertions

- ALWAYS: `/create-skill` applies every `/skill-standards` rule to the finished bundle and passes the target repository's deterministic skill checks, then returns the bundle ready for independent verification; it never dispatches `skill-auditor`, never invokes `/audit-skill`, and never waits on an audit verdict.
- ALWAYS: `/create-skill` carries no audit route; a repair request supplies the findings of a sealed audit run, and `/create-skill` repairs each finding and every same-class instance in the bundle, then returns the bundle ready for independent verification.
- ALWAYS: `/audit-skill` records one changeset-scoped `spx verification run` over the target bundle's files the changeset changes, with one unit per changed bundle file keyed by its audit class, audit kind, and path, and each finding keyed by its unit's key and its rule ID; a target bundle the changeset leaves unchanged returns a blocked result naming that bundle, and no run starts.
- ALWAYS: every rule ID `/audit-skill` records names a rule in the rule catalog `/skill-standards` or `/agent-prompt-standards` owns, and a defect neither catalog names is recorded as a `filed` finding under the catalog's `standard-gap` rule, which rejects nothing.
- ALWAYS: the rule catalogs `/skill-standards` and `/agent-prompt-standards` own give each rule `/audit-skill` enforces one stable rule ID and severity, and the auditor skeleton requires a run-recording auditor to key each unit by its subject and concern and each finding by its unit's key and rule ID, never by an ordinal.
- ALWAYS: a composing skill names each static dependency — one `plugin:skill` name with no argument — through the shared `require_skill` directive, states a dependency that carries an argument or a run-time-resolved name as the owned `Use skill` sentence with that value in place, and declares skill-use capability through the optional `tool('use_skill')` frontmatter token, so every generated agent surface receives its native instruction and capability set.

### Compliance

- ALWAYS: skill-authoring and audit guidance forbids model and reasoning
  overrides in skill frontmatter; a skill retains its invoking agent session's
  configuration in every supported product, including when invoked by a
  configured subagent, per `spx/15-subagent-execution.pdr.md` ([audit])
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
- ALWAYS: `/skill-standards`' auditor skeleton admits a sealed `spx verification run` projection as an auditor's verdict format ([audit])

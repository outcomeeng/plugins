---
malleability: spec
---

# Skills

PROVIDES the meta-skills that create, standardize, and audit SKILL.md files
SO THAT plugin authors
CAN produce skills that conform to the Agent Skills open standard and activate reliably at runtime

The skills-about-skills cluster is three peers with distinct roles:

- `/author-skill` routes skill creation, editing, improvement, and repair through typed workflows — builder, reference, validator, router — and returns a finished bundle ready for independent verification.
- `/skill-standards` owns the canonical rules and their rule catalog — frontmatter, XML structure, naming, progressive disclosure, skill types, reference patterns, code-fence and bash constraints, validation, script testing. Loaded by the other two.
- `/audit-skill` judges the skill files a changeset changes against the `/skill-standards` and `/agent-prompt-standards` rule catalogs, recording a sealed verification run and modifying no subject or product file.

## Assertions

### Compliance

- ALWAYS: a composing skill names each static dependency — one `plugin:skill` name with no argument — through the shared `require_skill` directive, states a dependency that carries an argument or a run-time-resolved name as the owned `Use skill` sentence with that value in place, and declares skill-use capability through the optional `tool('use_skill')` frontmatter token, so every generated agent surface receives its native instruction and capability set ([audit])
- ALWAYS: `/author-skill` applies the `/skill-standards` and `/agent-prompt-standards` rule catalogs to the bundle it produces or improves and returns that bundle ready for independent verification ([audit])
- ALWAYS: `/author-skill` carries no route that dispatches a skill auditor or waits on an audit verdict, and it repairs a bundle from supplied findings through a repair workflow that repairs and exercises the bundle before validating it ([audit])
- ALWAYS: `/skill-standards` and `/agent-prompt-standards` each own one rule catalog that gives every rule one stable identifier and one severity, and the `/skill-standards` auditor skeleton keys each finding by its unit and its catalog rule identifier ([audit])
- ALWAYS: `/skill-standards`' auditor skeleton admits a sealed `spx verification run` projection as an auditor's verdict format, in which each finding's key names its catalog rule identifier ([audit])
- ALWAYS: `/audit-skill` records one changeset-scoped verification run with one unit for each changed file under the bundle directory and one for each changed authored shared fragment the bundle includes, directly or through a nested include, every unit keyed `instructions:skill:file:<path>`, keys each finding `<unit>:<rule-id>`, and returns `BLOCKED` when the changeset changes neither a bundle file nor an included fragment or a governing standard is unreadable ([audit])
- ALWAYS: every rule identifier `/audit-skill` records names a rule in the `/skill-standards` or `/agent-prompt-standards` rule catalog, and no finding is recorded under an identifier outside those catalogs ([audit])
- ALWAYS: `/audit-skill` rejects only on touched text inside each changed file, and returns each other finding as `filed`, per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) ([audit])
- ALWAYS: `/author-skill`'s repair workflow repairs each supplied finding across every instance the cited clause covers and nothing the clause does not require, checks every same-class site and every dependency the repair changes before it returns the repaired bundle, and returns with the bundle, for each repair, the clause it applies and the check that shows the class closed ([audit])

- ALWAYS: skill-authoring and audit guidance forbids model and reasoning
  overrides in skill frontmatter; a skill retains its invoking agent session's
  configuration in every supported product, including when invoked by a
  configured subagent, per [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) ([audit])
- ALWAYS: `/skill-standards` owns every rule `/audit-skill` enforces — standards and enforcement stay in one place so drift cannot open between them ([audit])
- ALWAYS: `/author-skill` and `/audit-skill` load `/skill-standards` before doing any authoring or evaluation work — prevents memory-based assessment ([audit])
- ALWAYS: a skill governs its own behavior and remains independent of the agent, skill, or context that invokes it ([audit])
- ALWAYS: the `/skill-standards` caller-independence rule reads the payload scratch-directory fallback location a skill selects by harness environment, as [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) requires, as a property of the run and never as dependence on the caller ([audit])
- ALWAYS: `/skill-standards` requires a workflow step writing outside the invocation checkout to obtain confirmation naming the absolute destination before that write, and `/audit-skill` flags an unconfirmed one as blocking — resolving a path establishes where it is, never permission to write there ([audit])
- NEVER: `/skill-standards` permits skill content that frames a permission prompt, sandbox refusal, or tool-layer decline as an obstacle and documents a route around it, and `/audit-skill` flags such content as blocking — a documented bypass turns one operator's approval into a standing one for every session that loads the skill ([audit])
- ALWAYS: before proposing or applying a skill rename, `/author-skill` classifies every skill the repository requires reviewing by current name, skill type, governing naming form, proposed name or keep disposition, and reason; it reads declared methodology vocabulary and relevant file history before calling a name defective, and never infers a batch rename from a shared token, suffix, or grammatical number ([audit])
- NEVER: a skill names, describes, detects, constrains, refuses, branches on, or otherwise depends on its caller — context placement and dispatch policy belong to the caller ([audit])
- NEVER: block model invocation of a skill an agent preloads with `disable-model-invocation` — it also blocks that preload and skill-to-skill loading ([audit])
- NEVER: restate `/skill-standards` rules inside `/author-skill` or `/audit-skill` — a single source of truth prevents drift between standard and enforcer ([audit])
- NEVER: add standards content to `/create-skill/references/` — that directory carries workflow guidance; standards belong in `/skill-standards` ([audit])
- ALWAYS: when a foundation skill loads the same references on every invocation, `/skill-standards` requires one consolidated canonical eager payload and governs its total loaded size instead of applying the 500-line overview rule; conditional operational detail, templates, examples, and overlays remain separate ([audit])
- ALWAYS: `/skill-standards` states the guard-block rule the generated router states — a block on a command holding one operation with every string written literally ends its family, a block on a command whose composition the parts cannot carry — a process substitution, a pipe between two operations, a background `&`, a subshell, or a list that mixes `&&` and `||` — ends it too, and a block on a compound command runs its parts again one at a time, in their original order, with every string written literally ([audit])
- ALWAYS: The skill standard admits a bundled script's `__file__`-relative import of a sibling skill's script inside the same plugin, as a typed operation, and bans any path into another plugin's files or the plugin cache ([audit])
- ALWAYS: the skill audit, the auditor skeleton of the skill standard and the auditor template of the skill-creation guidance record the start input they build, each scope-add payload and each finding-add payload through a file written with the file-write tool in the session scratch directory and passed by path as the skill standard's payload-path rule states, the auditor skeleton passes a start input a bundled script writes, or the audited file a file-scoped run takes as its input, by that path written out literally, the auditor template passes its target file as the start input by that path written out literally, run every run-recording command as its own command that stops the audit on a nonzero exit other than the one rerun the payload-path rule allows, teach no heredoc and no pipe-built payload, and the skill auditor's definition grants the file-write tool and no stage that builds a payload in the shell ([audit])
- ALWAYS: the skill standard requires an audit skill that passes payload files to run-recording commands to add the harness's file-write tool beside its read tools, states that the tool writes only payload files in the session scratch directory, and states that the audit changes no file beyond those payload files and the run journal its own recording commands write ([audit])
- ALWAYS: the skill standard's payload-path rule requires an audit skill that passes payload files it writes with the file-write tool to run-recording commands to copy the scratch directory the harness names into each payload path character for character; when a file-write result reports a path that the scratch directory does not contain by whole path components, to stop before the command that reads that file, naming the reported path; to pass each run-recording command its payload path exactly as the file-write result reports it, written out literally as the argument; and, when a command exits nonzero with a diagnostic that names its payload file as absent, to run that command once more with the path copied from the file-write result and, on a second failure, to stop with its blocked result naming the run token; no payload path is retyped from memory; and a file a bundled script writes at a path the skill names is passed by that path written out literally, its command running no second time on a diagnostic that names that file as absent ([audit])
- ALWAYS: the skill-authoring skill ships under the one name `/author-skill`, the instructions plugin changelog maps `create-skill` to it, and every reference to it outside the plugin changelogs and the retained artifacts of attested runs uses that name ([audit])

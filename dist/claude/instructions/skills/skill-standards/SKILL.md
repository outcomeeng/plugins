---
name: skill-standards
user-invocable: false
description: >-
  Skill authoring standards enforced across all creating and auditing skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The canonical standards for skill authoring — frontmatter, XML structure, naming, descriptions, progressive disclosure, skill types, reference patterns, code-fence and bash constraints, validation, and script testing.
</objective>

<success_criteria>
Skills conform to these standards when, at minimum: (a) SKILL.md is under 500 lines unless it qualifies for the eager-foundation exception in `<progressive_disclosure>`, (b) the body uses pure XML structure with no markdown headings, (c) `<objective>` and `<success_criteria>` tags are present, (d) the description matches the invocation path — directive when description-match activation applies, passive when invoked only by exact name or a parent capability — (e) the skill is independent of its caller, and (f) the skill passes `/audit-skill` with no must-fix items.
</success_criteria>

<reference_note>
This is a reference skill. Composing skills invoke these standards explicitly before authoring or auditing. It is not a standalone workflow.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, check for `spx/local/skills.md` at the repository root. Read that file after this reference if it exists and apply it as the repo-local specialization (e.g., marketplace-specific naming conventions or additional constraints). A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<skill_organization>

Skills follow a **reference pattern** to avoid duplication:

1. **Foundational skill** (e.g., `/test`) — core principles and domain-agnostic patterns.
2. **Language-specific skills** (e.g., `/test-python`, `/test-typescript`) — reference the foundational skill, provide only language-specific implementations.
3. **Reference skills** (e.g., `/typescript-standards`, `/skill-standards`) — standards explicitly invoked by composing skills, never selected as standalone user workflows.

For language-specific skill prose that references a foundation, use the unqualified invocation name (`/test`) so it resolves to whichever foundational skill is installed.

**Skill-tool composition:** A skill may invoke another skill when the parent workflow explicitly composes that capability. Composition obeys these limits:

1. The parent carries the runtime's skill-invocation capability in `allowed-tools` and names the exact installed skill to invoke.
2. The target remains callable through the active runtime's skill-invocation surface; no runtime setting may block composed or reference-skill invocation.
3. The parent owns sequencing, validates the returned shape, and merges the child result into its own output contract.
4. A composition step invokes only capabilities required by the workflow; it never discovers or invokes adjacent skills speculatively.
5. Reference-only prose may name foundational concepts without invocation, while reference skills are loaded through the runtime's skill-invocation capability when their full standards govern the work.

**Caller independence:** A skill governs its own behavior and nothing else. It never names, describes, detects, constrains, refuses, branches on, or otherwise depends on the agent, skill, or context that invokes it. The dependency runs one way: a caller may know the skill it invokes; the skill never knows its callers.

Context placement, agent selection, and dispatch policy belong to the caller. A skill remains independently invocable even when the product normally reaches it through an agent or another skill. Correct an invalid invocation in the router, agent, or composing skill that made the decision; never add a dispatch gate or caller check to the invoked skill.

</skill_organization>

<frontmatter>

Every SKILL.md starts with YAML frontmatter. The canonical catalog of supported fields lives in the Claude Code docs at <https://code.claude.com/docs/en/skills#frontmatter-reference>. Read the docs page when a question is about execution behavior; read this section when it is about how this marketplace authors skills.

| Field                      | Required    | Constraint                                                                                                                                                                                                                        |
| -------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                     | No          | Lowercase letters, numbers, hyphens. ≤64 chars. Must match the directory name when set. If omitted, the directory name is used.                                                                                                   |
| `description`              | Recommended | Directive style for invoked skills (see `<descriptions>`); passive for references. Combined with `when_to_use` the listing is capped at 1,536 chars; put the key trigger first.                                                   |
| `when_to_use`              | No          | Extra trigger phrases or example requests appended to `description` in the skill listing. Shares the 1,536-char cap.                                                                                                              |
| `argument-hint`            | No          | Free-text hint shown during `/` autocomplete (e.g. `[issue-number]`).                                                                                                                                                             |
| `arguments`                | No          | Named positional arguments for `$name` substitution in the body. Space-separated string or YAML list; names map to argument positions in order.                                                                                   |
| `allowed-tools`            | No          | Tools Claude may use without per-call approval while the skill is active. Space-separated string or YAML list. Restrict for audit (read-only) and reference skills.                                                               |
| `disable-model-invocation` | No          | `true` to **block programmatic invocation entirely** — Claude cannot load the skill, including via the Skill tool, and the skill cannot be preloaded into subagents. Use for `/deploy`-style user-only commands. Default `false`. |
| `user-invocable`           | No          | `false` to hide from the `/` autocomplete menu while keeping Claude able to invoke via the Skill tool. Description stays in context. Use for reference skills that other skills load programmatically. Default `true`.            |
| `model`                    | No          | Model override for this skill (`opus`, `sonnet`, `haiku`, or `inherit`). Marketplace verification-sensitive surfaces use explicit `sonnet` and never use session inheritance.                                                     |
| `effort`                   | No          | Effort level (`low`, `medium`, `high`, `xhigh`, `max`) — overrides the session effort while the skill is active.                                                                                                                  |
| `context`                  | No          | `fork` to run the skill in a forked subagent context. Combine with `agent`.                                                                                                                                                       |
| `agent`                    | No          | Subagent type to use when `context: fork` is set (`Explore`, `Plan`, `general-purpose`, or a custom agent). Defaults to `general-purpose`.                                                                                        |
| `hooks`                    | No          | Hooks scoped to this skill's lifecycle. See the Claude Code hooks reference for shape.                                                                                                                                            |
| `paths`                    | No          | Glob patterns that limit auto-activation to matching files. Comma-separated string or YAML list.                                                                                                                                  |
| `shell`                    | No          | `bash` (default) or `powershell` for the skill's inline and fenced command-injection blocks. The `powershell` value requires `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`.                                                                 |

**Visibility vs invocability.** Two fields gate how a skill is reached. They are not aliases — pick deliberately. Automation re-entry — a scheduled wakeup, heartbeat, or `/loop` — arrives as a user-style prompt because the harness offers no Claude-private heartbeat, so it follows the `User /skill` column exactly:

| Frontmatter                      | User `/skill` | Claude (Skill tool) | Subagent preload | Automation re-entry | Description in context |
| -------------------------------- | ------------- | ------------------- | ---------------- | ------------------- | ---------------------- |
| *(default)*                      | Yes           | Yes                 | Yes              | Yes                 | Always                 |
| `disable-model-invocation: true` | Yes           | **No**              | **No**           | Yes                 | Not in context         |
| `user-invocable: false`          | **No**        | Yes                 | Yes              | **No**              | Always                 |

Pick the gate by role:

- A reference skill another SKILL.md loads via the Skill tool, or a background-knowledge skill, uses `user-invocable: false` — hidden from the `/` menu, still loadable by Claude and preloadable into subagents.
- A user-only side-effecting command (`/deploy`) uses `disable-model-invocation: true`. NEVER set it on a skill other skills or subagents must load: it blocks the Skill-tool call (surfacing `Skill <name> cannot be used with Skill tool due to disable-model-invocation`) AND blocks subagent preloading.
- A skill any automation loop re-enters — a scheduled wakeup, heartbeat, or `/loop` target — MUST be user-invocable (leave the default; never `user-invocable: false`). Automation fires as a user-style prompt, so `user-invocable: false` rejects it and no Claude-private heartbeat exists to bypass that. When a loop body is otherwise reference-like, expose a user-invocable entry the loop targets rather than gating the body. Such a loop body keeps a **passive** description — it is invoked by exact name (the timer or a parent skill), not by description-match, so a directive description would only cause false auto-activations. A user-invocable skill with a passive description is the correct shape here, not a defect.

Audit skills (`audit-*`) must add `allowed-tools: Read, Grep, Glob, Bash` per the read-only rule for audit skills, plus `Skill` when the audit composes another skill — audit runs never modify files.

**Directory match is mandatory.** `skills/author/` → `name: author`. A mismatch breaks skill lookup.

**Field `skills:` is NOT supported on SKILL.md.** It exists only on subagent definitions (`agents/*.md`), where it preloads skill content as reference material into the subagent's startup context. The official docs page above lists every field a SKILL.md actually accepts; `skills:` is not among them. To make a reference skill available to another skill, set `user-invocable: false` on the reference and have the parent invoke it by installed name through the runtime's skill-invocation surface — there is no preload field on the consumer side.

**Command-capability fields.** A SKILL.md carries every capability a slash command had — `argument-hint`/`arguments`, `allowed-tools` restriction, plus `!`-dynamic context and `@` file references in the body. The authoring and audit rules for that surface live in `${CLAUDE_SKILL_DIR}/references/command-capabilities.md`; read it before authoring a skill that takes arguments, injects state, or restricts tools.

</frontmatter>

<naming_conventions>

The `name` field is the user invocation path (`/skill-name`). Match user speech patterns.

**Rules:**

- Use domain acronyms: `author` not `author-spec-tree-artifacts`
- Use terms users actually say: `test-python` not `python-unit-test-framework`
- Think "CD-ROM" not "Compact Disc Read Only Memory"
- Directory name MUST match: `skills/author/` → `name: author`

**Naming form:** invoked workflow skills use imperative verbs. Reference skills use noun phrases ending in the domain they standardize, such as `skill-standards` or `typescript-test-standards`.

**Vocabulary precedence:** Skill-name grammar does not override declared methodology vocabulary. When a term can belong both to a skill-name form and to another taxonomy, read the source that declares that taxonomy and inspect file history before calling the term a naming defect.

Treat generated runtime output and implementation names as lower-layer evidence, never as the authority for vocabulary classification.

```yaml
# ✅ Matches user speech
name: author # Users say "author a spec"
name: test-typescript # Users say "test TypeScript code"
name: bootstrap # Users say "bootstrap the spec tree"

# ❌ Nobody says these
name: author-spec-tree-artifacts # Too verbose
name: typescript-unit-framework # Wrong order
```

</naming_conventions>

<descriptions>

The description field governs skill selection. Claude has a character budget for all skill metadata — when exceeded, skills become invisible.

**Activation rates by style** (Seleznov, 650 automated trials, Feb 2026):

| Style         | Activation | Pattern                          |
| ------------- | ---------- | -------------------------------- |
| Passive       | ~77%       | `Use when…`                      |
| Expanded      | ~93%       | `…or any X-related task`         |
| **Directive** | **~100%**  | `ALWAYS invoke… NEVER X without` |

**Use directive descriptions for invoked skills:**

```yaml
description: >-
  ALWAYS invoke this skill when <triggers>.
```

**NEVER constraint — add only when it disambiguates.** A NEVER line helps when:

- The skill is the only one with that negative (e.g., `NEVER work on the spec tree without loading context` — only contextualizing says this).
- Claude has a strong built-in alternative the negative prevents (e.g., `NEVER run git commit without this skill` — Claude would just run `git commit` directly).

Omit NEVER when multiple skills share the same negative (adds noise) or the ALWAYS trigger is already specific enough.

**Language-after-artifact** (matches user speech):

```yaml
# ✅ "audit ADRs for Python"
ALWAYS invoke this skill when auditing ADRs for Python.

# ❌ "audit Python ADRs"
ALWAYS invoke this skill when auditing Python ADRs.
```

**Match user speech over formal jargon:** Use abbreviations users would use (ADR not Architecture Decision Record). Avoid corporate speak.

**Reference skills** use `user-invocable: false` with a passive description:

```yaml
user-invocable: false
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
```

**Protocol and loop-body skills** that a parent skill loads, or that a timer fires by exact name (a heartbeat re-entry target), keep a passive description while staying user-invocable — they are never reached by description-match, so a directive description would only cause false auto-activations. See the gate-by-role rules in `<frontmatter>`.

**Audit skills** describe the audit they perform: the subject, judgment, and distinguishing criteria. Their descriptions contain no routing, dispatch, preload, agent, or execution-context statement. Audit skills stay model-invocable, carry read-only `allowed-tools`, and never use `disable-model-invocation`.

```yaml
description: >-
  Test-evidence audit methodology — judges test evidence against the assertions
  it claims to verify, covering source ownership, coupling, falsifiability, and
  full-chain coverage.
```

**Conflict resolution:** If Claude picks the wrong skill, descriptions are too similar. Make trigger terms distinct — "sales data in Excel" vs "log files and system metrics".

</descriptions>

<xml_structure>

Skills use **pure XML structure** — no markdown headings (`#`, `##`, `###`) anywhere in the body. Keep markdown formatting *within* content (bold, italic, lists, tables, code blocks, links).

**Why pure XML:** unambiguous section boundaries, consistent cross-skill structure, better token efficiency, and more reliable runtime interpretation.

**Required tags (every skill):**

| Tag                  | Content                                                                                                                                                                                       |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<objective>`        | The observable **output** the skill produces, in a definite shape — one sentence, not an actor or an activity, not a summary of the skill. See `/agent-prompt-standards` `<objective_shape>`. |
| `<success_criteria>` | The properties that prove the output is sound — not a re-list of the workflow steps.                                                                                                          |

**Router-pattern tags** (skills that route to multiple workflows):

| Tag                      | Content                                                          |
| ------------------------ | ---------------------------------------------------------------- |
| `<essential_principles>` | Principles that apply regardless of which workflow runs. Inline. |
| `<intake>`               | Question to ask the user to determine routing.                   |
| `<routing>`              | Table mapping responses to workflow files.                       |
| `<reference_index>`      | List of available reference files.                               |
| `<workflows_index>`      | List of available workflow files.                                |

**Workflow-file tags** (files inside `workflows/`):

| Tag                  | Content                                                     |
| -------------------- | ----------------------------------------------------------- |
| `<required_reading>` | Which reference files to load before running this workflow. |
| `<process>`          | Step-by-step procedure.                                     |
| `<success_criteria>` | When this workflow is complete.                             |

**Conditional tags** (include when the skill's complexity or purpose calls for them):

| Tag                    | When to include                                                                                                                                |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `<quick_start>`        | On-demand tool skills with a meaningful fast path. **Omit** for foundation, gate, validator, and reference skills — completeness is the point. |
| `<context>`            | Background needed before starting.                                                                                                             |
| `<workflow>`           | Sequential steps (non-router skills).                                                                                                          |
| `<advanced_features>`  | Progressive disclosure for deep-dive topics.                                                                                                   |
| `<validation>`         | Verification checks.                                                                                                                           |
| `<examples>`           | Input/output pairs.                                                                                                                            |
| `<anti_patterns>`      | Common mistakes to avoid.                                                                                                                      |
| `<security_checklist>` | Skills with security implications.                                                                                                             |
| `<testing>`            | Testing workflows or validation steps.                                                                                                         |
| `<common_patterns>`    | Reusable recipes.                                                                                                                              |
| `<reference_guides>`   | Pointers to detailed reference files.                                                                                                          |
| `<failure_modes>`      | Named failures from actual usage — what happened, why, how to avoid.                                                                           |

This table is representative, not exhaustive: a skill may add semantically named domain sections beyond it (this file's `<frontmatter>`, `<descriptions>`, and reference-pointer sections such as `<platform_constraints>` and `<script_standards>` are examples).

**Nesting:** XML tags can nest for hierarchical content.

```text
<examples>
  <example number="1">
    <input>User input</input>
    <output>Expected output</output>
  </example>
</examples>
```

**Close every tag.** Unclosed tags break parsing.

**`<context>` bash blocks fire on every skill load.** Every `!`command`` line inside `<context>` runs unconditionally each time the skill is invoked — including false-positive activations triggered by directive descriptions matching adjacent terms. Heavy commands (session lists, full file contents, cache enumerations) compound the per-load tax.

Constraints:

- Filter expensive commands (`spx session list --status doing,todo`, `git log -10`, `head -N`) so output stays bounded.
- Move data into the workflow file that actually consumes it when the skill loader doesn't need it for trigger evaluation. The `<context>` block is for trigger-time orientation, not workflow inputs.
- Avoid commands whose output grows monotonically (archives, full caches, full file trees).

**Semantic names:** `<workflow>` not `<steps>`, `<success_criteria>` not `<done>`, `<anti_patterns>` not `<dont_do>`.

**Reference tags in prose by name:** "Using the schema in `<schema>` tags…", "Follow the workflow in `<workflow>`…". Makes structure self-documenting.

**Intelligence rules** — match structure to complexity:

| Skill class                      | Expected tags                                                                                                                                                           |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Simple (single domain)           | `<objective>`, `<success_criteria>`, optionally `<quick_start>`                                                                                                         |
| Medium (multiple patterns)       | Required + `<workflow>` and/or `<examples>`                                                                                                                             |
| Complex (multi-domain, API, sec) | Required + router pattern + appropriate conditional tags                                                                                                                |
| Foundation / gate / validator    | Required + `<workflow>`. **Omit** `<quick_start>` — no abbreviated path exists.                                                                                         |
| Reference                        | Required; add `<workflow>` only when the reference defines an ordered procedure. A declarative standards or vocabulary catalog omits procedural tags.                   |
| Auditor (agent-preloaded)        | The canonical auditor skeleton — **read** `${CLAUDE_SKILL_DIR}/references/auditor-skeleton.md` when authoring or auditing an `audit-*` skill. **Omit** `<quick_start>`. |

Don't over-engineer simple skills. Don't under-specify complex ones.

</xml_structure>

<eager_foundation_exception>

When a foundation skill requires the same material on every fresh invocation, inline that canonical material and govern the total eager payload instead of the SKILL.md line count. The exception requires the same material on every invocation, removal of mandatory secondary reads, separate conditional detail, internal consistency, improved effectiveness, and a rendered payload of at most 40,000 Unicode code points measured by every audit. Never use it to inline optional detail or avoid routing.

This skill invokes the exception for itself. An author needs its structure table, its command-capability rules, and its path boundary on one invocation, and each of its six references carries conditional detail rather than a mandatory read. Measure the skill as installed, which is the payload an invocation loads:

```bash
python3 -c "from pathlib import Path; print(len(Path('${CLAUDE_SKILL_DIR}/SKILL.md').read_text(encoding='utf-8')))"
```

</eager_foundation_exception>

<progressive_disclosure>

SKILL.md is an overview. Reference files carry detail. Claude loads reference files only when needed.

**Rules:**

- Keep SKILL.md under 500 lines unless the eager-foundation exception below applies.
- References live in `references/` one level deep from SKILL.md. Do not nest references that read other references — Claude may only partially read transitive files.
- Reference files over 100 lines need a table of contents at the top, so partial reads still see the full scope.
- Use forward slashes in every path — `references/guide.md`, never `references\guide.md`. Works across platforms.

Apply `<eager_foundation_exception>`. A 500-line overview followed immediately by mandatory references is not progressive disclosure; total eagerly loaded content is the relevant cost.

**Token efficiency:** simple task loads SKILL.md only (~500 tokens); medium loads SKILL.md + one reference (~1000); complex loads SKILL.md + multiple (~2000+).

```text
✅ One level deep
SKILL.md → references/advanced.md (complete info)
         → references/examples.md (complete info)

❌ Nested
SKILL.md → references/advanced.md → references/details.md → actual info
```

**Name reference files descriptively** — `xml-structure-examples.md`, not `examples.md`. The filename is also a table-of-contents entry in `<reference_index>`.

**Every reference file must be cited.** A file in `references/` that is not mentioned by SKILL.md or any workflow file is orphaned — it costs ~1,800+ tokens per speculative read (Claude tends to open siblings of cited references) and signals either dead content or a missing cross-reference. Either delete the file or add an explicit `<required_reading>` from the workflow that needs it. Verify before committing: `grep -rn "<filename>" <skill-dir>/`.

</progressive_disclosure>

<conciseness>

The context window is shared. A skill competes for tokens with the system prompt, conversation history, other skills' metadata, and the user's request.

**Test every sentence:** "Does removing this reduce the skill's effectiveness at the task?" If no — cut it.

**What the executing runtime already knows (never include):**

- General programming knowledge
- Language syntax and standard-library APIs
- Common design patterns
- How to use its own tools

**What the executing runtime needs (include):**

- Product-specific conventions that contradict common patterns
- Domain knowledge not in training data
- Failure modes from actual usage (not hypotheticals)
- Verification commands and thresholds

**Concrete over abstract:**

```text
❌ "Ensure coverage is maintained"
✅ "Coverage delta must be ≤0.5%. Run: pnpm test --coverage | grep target.ts"
```

**When to elaborate:** the concept is domain-specific (not general programming), the pattern is non-obvious or counterintuitive, or context affects behavior in subtle ways.

</conciseness>

<skill_types>

Six skill types. Each has a distinct purpose and primary output.

| Type           | Purpose                      | Primary output                    | Key sections                                                                                                                                             |
| -------------- | ---------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Builder**    | Create new artifacts         | Code, documents, widgets, configs | Required clarifications, output spec, domain standards, templates in `assets/`                                                                           |
| **Guide**      | Teach procedures             | Step-by-step workflows, tutorials | Numbered workflow, input→output example pairs, decision trees                                                                                            |
| **Automation** | Execute multi-step processes | Processed files, transformed data | Tested scripts in `scripts/`, error handling, dependencies, I/O contracts                                                                                |
| **Analyzer**   | Extract insights             | Reports, summaries, reviews       | Analysis scope, evaluation criteria, output format, synthesis                                                                                            |
| **Validator**  | Enforce quality              | Pass/fail verdicts, scores        | Criteria with thresholds, scoring rubric, remediation guidance; `user-invocable: false` when invoked only by agents or explicit runtime skill invocation |
| **Reference**  | Share domain knowledge       | Standards loaded by other skills  | `user-invocable: false`, passive description, `allowed-tools: Read`                                                                                      |

**Type-selection rule of thumb:**

- Creates new artifacts → Builder
- Teaches how-to → Guide
- Executes processes → Automation
- Extracts insights → Analyzer
- Checks quality → Validator
- Shares knowledge multiple skills need → Reference

</skill_types>

<reference_skills>

Reference skills hold shared domain knowledge that multiple skills need. Consuming workflows explicitly invoke them through the runtime's documented skill-composition surface. A `/skill-name` mention in prose records the dependency but never loads the reference.

**When to create a reference skill.** Two or more skills in the same plugin need the same domain knowledge (standards, patterns, anti-patterns, conventions). Alternatives fail: duplicating the content creates maintenance drift, and putting it in one skill's `references/` directory makes it unreachable from the other skill's `${CLAUDE_SKILL_DIR}`.

**Required frontmatter:**

```yaml
---
name: {domain}-standards
user-invocable: false
description: >-
  {Domain} standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---
```

- `user-invocable: false` — prevents false activations from user prompts.
- Passive description (no `ALWAYS`/`NEVER`) — directive descriptions trigger false activations for a reference.
- `allowed-tools: Read` — reference skills only read.

**How consuming skills reference it.** Name the reference skill in running text for traceability, then explicitly invoke it through the runtime's documented skill-composition surface before applying its rules. A bare `See /skill-name` instruction is insufficient.

```markdown
# In test-typescript/SKILL.md:

Invoke `/typescript-test-standards` through the runtime's skill-composition surface before applying its test file naming, execution-level, and reusable-pattern rules.

# In audit-typescript-tests/SKILL.md:

Before auditing, invoke `/typescript-test-standards` through the runtime's skill-composition surface and apply its complete catalog of TypeScript test rules.
```

**Naming convention:** `{domain}-standards` for standards. Examples: `typescript-test-standards`, `skill-standards`, `agent-prompt-standards`.

**Extraction completeness test.** When factoring a standards reference out of a builder/auditor pair, the extraction is complete only when the corresponding audit skill loads the new reference and nothing else for standards. If the auditor still reads files from the builder's `references/` directory for standards, content is still stranded there — finish the move. The same rule catches partial extractions: a standards file in a creator skill's `references/` directory that the auditor needs is a bug, not an architecture.

**Anti-patterns:**

- Directive descriptions (`ALWAYS`/`NEVER`) — cause false activations.
- Shared content buried in one skill's `references/` — the skill-directory token is isolated per skill.
- Same content duplicated across multiple `references/` — drifts.
- Partial extraction: naming a new standards skill while leaving the meat in the builder's `references/` — the auditor keeps reading the old location and the rename becomes a lie.

</reference_skills>

<templates_and_variables>

The runtime variable scopes and bundled-file path examples live in `${CLAUDE_SKILL_DIR}/references/runtime-variables.md`. Read it before referencing bundled files.

Hook authoring patterns — the `SessionStart` + `$CLAUDE_ENV_FILE` session-identity mechanism, hook `command:` paths, and the plugin `hooks/` directory layout — live in `${CLAUDE_SKILL_DIR}/references/plugin-hooks.md`. Read it before wiring hook commands.

</templates_and_variables>

<platform_constraints>

Two platform footguns affect skill authoring: dprint's `markup_fmt` handling of nested code fences, and Claude Code's bash-safety checker for `!` expansion. Read `${CLAUDE_SKILL_DIR}/references/platform-constraints.md` before using multi-backtick fences or `!` command syntax.

</platform_constraints>

<xml_tag_formatting>

**Always add a blank line before a closing pseudo-XML tag that follows an unordered list.** Without it, markdown parsers indent the closing tag as part of the last list item.

```text
# ❌ WRONG

<section>

- Item 1
- Item 2
</section>

# ✅ CORRECT

<section>

- Item 1
- Item 2

</section>
```

</xml_tag_formatting>

<script_standards>

Skills that ship `scripts/` must validate inputs with verbose, deterministic, actionable error messages and test every script before inclusion. The full validation-message and script-testing rules live in `${CLAUDE_SKILL_DIR}/references/script-standards.md`. Read it before authoring a skill that bundles scripts.

</script_standards>

<path_boundary>

A consumer's harness declares which directories a session may touch: the working directory, any additional working directories, the plugin's own files, and a scratch location. A skill instructs Claude, so every path a skill names becomes a path Claude writes — a skill that names a path outside that set directs the write out of the boundary the operator approved.

**Scratch storage comes from a unique-per-invocation source, never a named path.** Use `mktemp -d` or `mktemp -t` in shell and `tempfile.mkdtemp` or `TemporaryDirectory` in Python. Each derives a unique directory from the environment's own temporary root, so no skill ever needs to spell a temporary path. Never write `/tmp`, `/var/tmp`, `/private/var/tmp`, `~/tmp`, or a `${TMPDIR:-/tmp}` fallback: a fixed path is identical across concurrent invocations, so two runs of the same skill overwrite each other, and it sits outside the declared set. `mktemp` already resolves an unset `TMPDIR`, so the fallback spelling buys nothing and reintroduces the literal. Whichever step creates a scratch directory removes it on every exit path, including failure.

**A write outside the invocation checkout is confirmed before it happens, not resolved and taken.** A home-directory configuration path, another repository's checkout, or any location the operator did not name in the request needs confirmation that states the absolute destination. Being able to resolve a path is not authorization to write to it, and one confirmation covers one write — the next asks again. Prefer the in-checkout location whenever both exist, because a write there is reviewable in that repository's history.

One content may name a prohibited path: the rule prohibiting it. A standard listing the spellings an author may not write, or an audit row naming what to flag, states the rule rather than breaking it. Judge the surrounding intent — a path a skill presents as prohibited is not a violation, and a path a skill presents as a step to follow is one regardless of how it is fenced.

**A permission prompt is a result, not an obstacle.** When a tool layer declines a path, that decline is the boundary working. Never document a way around it — a shell redirect standing in for a refused tool write, a broader permission substituted for a narrow one, a path rewritten to dodge a check. Name a path inside the boundary instead. A skill that teaches evasion converts one operator's approval into every future session's bypass.

</path_boundary>

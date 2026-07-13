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
Skills conform to these standards when, at minimum: (a) the SKILL.md is under 500 lines, (b) the body uses pure XML structure with no markdown headings, (c) `<objective>` and `<success_criteria>` tags are present, (d) the description matches the invocation path — directive when description-match activation applies, passive when invoked only by exact name or a parent capability — and (e) the skill passes `/audit-skills` with no must-fix items.
</success_criteria>

<reference_note>
This is a reference skill. `/create-skills` and `/audit-skills` load these standards automatically. Do not invoke directly.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, check for `spx/local/skills.md` at the repository root. Read that file after this reference if it exists and apply it as the repo-local specialization (e.g., marketplace-specific naming conventions or additional constraints). A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<skill_organization>

Skills follow a **reference pattern** to avoid duplication:

1. **Foundational skill** (e.g., `/test`) — core principles and domain-agnostic patterns.
2. **Language-specific skills** (e.g., `/test-python`, `/test-typescript`) — reference the foundational skill, provide only language-specific implementations.
3. **Reference skills** (e.g., `/typescript-standards`, `/skill-standards`) — standards loaded by other skills, never invoked directly.

For language-specific skill prose that references a foundation, use the unqualified invocation name (`/test`) so it resolves to whichever foundational skill is installed.

**Skill-tool composition:** A skill may invoke another skill when the parent workflow explicitly composes that capability. Composition obeys these limits:

1. The parent carries the runtime's skill-invocation capability in `allowed-tools` and names the exact installed skill to invoke.
2. The target remains model-invocable; `disable-model-invocation: true` is forbidden on composed and reference skills.
3. The parent owns sequencing, validates the returned shape, and merges the child result into its own output contract.
4. A composition step invokes only capabilities required by the workflow; it never discovers or invokes adjacent skills speculatively.
5. Reference-only prose may name foundational concepts without invocation, while reference skills are loaded through the runtime's skill-invocation capability when their full standards govern the work.

</skill_organization>

<frontmatter>

Every Codex SKILL.md starts with YAML frontmatter and uses only fields accepted by Codex's current skill validator. `name` matches the skill directory, `description` states the selection contract, and tool restrictions grant only capabilities the workflow needs. Do not project Claude-only visibility, preload, heartbeat, hook, or invocation semantics onto Codex fields.

Reference skills stay hidden from ordinary user selection while remaining available to composed workflows through Codex's documented skill invocation surface. Audit skills remain read-only. A field or reachability behavior without a documented Codex contract is omitted.

Read `${SKILL_DIR}/references/command-capabilities.md` before authoring arguments, dynamic context, tool restrictions, or file references for Codex.

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

Descriptions state when Codex selects a skill and distinguish adjacent skills with concrete trigger terms. Use directive wording for description-match entry points and passive wording for references or protocols invoked by exact name. Keep the trigger first, avoid overlapping descriptions, and route isolated audits through their configured auditor role.

</descriptions>

<xml_structure>

Skills use **pure XML structure** — no markdown headings (`#`, `##`, `###`) anywhere in the body. Keep markdown formatting *within* content (bold, italic, lists, tables, code blocks, links).

**Why pure XML:** unambiguous section boundaries, consistent cross-skill structure, better token efficiency, better Claude performance.

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

| Tag                    | When to include                                                                                                                                                                                             |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<quick_start>`        | On-demand tool skills with a meaningful fast path. **Omit** for foundation, gate, validator, and reference skills — completeness is the point.                                                              |
| `<dispatch_gate>`      | Agent-preloaded audit skills. A hard stop at the top of the body that halts a main-conversation invocation and directs it to dispatch the corresponding auditor agent. **Omit** for every other skill type. |
| `<context>`            | Background needed before starting.                                                                                                                                                                          |
| `<workflow>`           | Sequential steps (non-router skills).                                                                                                                                                                       |
| `<advanced_features>`  | Progressive disclosure for deep-dive topics.                                                                                                                                                                |
| `<validation>`         | Verification checks.                                                                                                                                                                                        |
| `<examples>`           | Input/output pairs.                                                                                                                                                                                         |
| `<anti_patterns>`      | Common mistakes to avoid.                                                                                                                                                                                   |
| `<security_checklist>` | Skills with security implications.                                                                                                                                                                          |
| `<testing>`            | Testing workflows or validation steps.                                                                                                                                                                      |
| `<common_patterns>`    | Reusable recipes.                                                                                                                                                                                           |
| `<reference_guides>`   | Pointers to detailed reference files.                                                                                                                                                                       |
| `<failure_modes>`      | Named failures from actual usage — what happened, why, how to avoid.                                                                                                                                        |

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

| Skill class                      | Expected tags                                                                                                                                                    |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Simple (single domain)           | `<objective>`, `<success_criteria>`, optionally `<quick_start>`                                                                                                  |
| Medium (multiple patterns)       | Required + `<workflow>` and/or `<examples>`                                                                                                                      |
| Complex (multi-domain, API, sec) | Required + router pattern + appropriate conditional tags                                                                                                         |
| Foundation / gate / validator    | Required + `<workflow>`. **Omit** `<quick_start>` — no abbreviated path exists.                                                                                  |
| Reference                        | Required; add `<workflow>` only when the reference defines an ordered procedure. A declarative standards or vocabulary catalog omits procedural tags.            |
| Auditor (agent-preloaded)        | The canonical auditor skeleton — **read** `${SKILL_DIR}/references/auditor-skeleton.md` when authoring or auditing an `audit-*` skill. **Omit** `<quick_start>`. |

Don't over-engineer simple skills. Don't under-specify complex ones.

</xml_structure>

<progressive_disclosure>

Keep SKILL.md under 500 lines and move detailed patterns into descriptively named files one level below `references/`. Cite every bundled reference from the skill or the workflow that requires it. Avoid nested reference chains, orphaned files, and duplicated standards.

</progressive_disclosure>

<conciseness>

The context window is shared. A skill competes for tokens with the developer instructions, conversation history, other skills' metadata, and the user's request.

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

| Type           | Purpose                      | Primary output                    | Key sections                                                                                                                                        |
| -------------- | ---------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Builder**    | Create new artifacts         | Code, documents, widgets, configs | Required clarifications, output spec, domain standards, templates in `assets/`                                                                      |
| **Guide**      | Teach procedures             | Step-by-step workflows, tutorials | Numbered workflow, input→output example pairs, decision trees                                                                                       |
| **Automation** | Execute multi-step processes | Processed files, transformed data | Tested scripts in `scripts/`, error handling, dependencies, I/O contracts                                                                           |
| **Analyzer**   | Extract insights             | Reports, summaries, reviews       | Analysis scope, evaluation criteria, output format, synthesis                                                                                       |
| **Validator**  | Enforce quality              | Pass/fail verdicts, scores        | Criteria with thresholds, scoring rubric, remediation guidance; `user-invocable: false` when invoked only by agents or explicit `Skill(name)` calls |
| **Reference**  | Share domain knowledge       | Standards loaded by other skills  | `user-invocable: false`, passive description, `allowed-tools: Read`                                                                                 |

**Type-selection rule of thumb:**

- Creates new artifacts → Builder
- Teaches how-to → Guide
- Executes processes → Automation
- Extracts insights → Analyzer
- Checks quality → Validator
- Shares knowledge multiple skills need → Reference

</skill_types>

<reference_skills>

Reference skills hold shared domain knowledge that multiple skills need. They are **not** invoked directly — consuming skills reach them via `/skill-name` references in their text.

**When to create a reference skill.** Two or more skills in the same plugin need the same domain knowledge (standards, patterns, anti-patterns, conventions). Alternatives fail: duplicating the content creates maintenance drift, and putting it in one skill's `references/` directory makes it unreachable from the other skill's `${SKILL_DIR}`.

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

**How consuming skills reference it.** Write the reference skill path in running text and invoke it through the runtime's documented skill-composition surface.

```markdown
# In test-typescript/SKILL.md:

See `/typescript-test-standards` for test file naming, execution levels, and reusable test patterns.

# In audit-typescript-tests/SKILL.md:

Before auditing, read `/typescript-test-standards` for the complete catalog of TypeScript test rules.
```

**Naming convention:** `{domain}-standards` for standards. Examples: `typescript-test-standards`, `skill-standards`, `agent-prompt-standards`.

**Extraction completeness test.** When factoring a standards reference out of a builder/auditor pair, the extraction is complete only when the corresponding audit skill loads the new reference and nothing else for standards. If the auditor still reads files from the builder's `references/` directory for standards, content is still stranded there — finish the move. The same rule catches partial extractions: a standards file in a creator skill's `references/` directory that the auditor needs is a bug, not an architecture.

**Anti-patterns:**

- Directive descriptions (`ALWAYS`/`NEVER`) — cause false activations.
- Shared content buried in one skill's `references/` — `${SKILL_DIR}` is isolated per skill.
- Same content duplicated across multiple `references/` — drifts.
- Partial extraction: naming a new standards skill while leaving the meat in the builder's `references/` — the auditor keeps reading the old location and the rename becomes a lie.

</reference_skills>

<templates_and_variables>

Reference skill-bundled files with the Codex skill-directory token. Its scope and bundled-file examples live in `${SKILL_DIR}/references/runtime-variables.md`. This standard declares no Codex hook-command or plugin-root variable until Codex documents that contract.

Read `${SKILL_DIR}/references/plugin-hooks.md` for the explicit boundary between Claude hook contracts and Codex's runtime-provided session identity; do not project Claude hook fields or variables onto Codex.

</templates_and_variables>

<platform_constraints>

Read `${SKILL_DIR}/references/platform-constraints.md` before using multi-backtick fences. Apply only constraints that the reference identifies for Codex.

</platform_constraints>

<xml_tag_formatting>

**Always add a blank line before a closing pseudo-XML tag that follows an unordered list.** Without it, markdown parsers indent the closing tag as part of the last list item.

```markdown
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

Skills that ship `scripts/` must validate inputs with verbose, deterministic, actionable error messages and test every script before inclusion. The full validation-message and script-testing rules live in `${SKILL_DIR}/references/script-standards.md`. Read it before authoring a skill that bundles scripts.

</script_standards>

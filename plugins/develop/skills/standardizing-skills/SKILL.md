---
name: standardizing-skills
disable-model-invocation: true
description: >-
  Skill authoring standards enforced across all creating and auditing skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical standards for skill authoring. Every rule that `/auditing-skills` enforces lives here — frontmatter, XML structure, naming, descriptions, progressive disclosure, skill types, reference patterns, code-fence and bash constraints, validation, script testing. `/creating-skills` loads this reference before authoring; `/auditing-skills` loads it before evaluating. Nothing in this skill is optional for the skills that load it.
</objective>

<success_criteria>
Skills conform to these standards when, at minimum: (a) the SKILL.md is under 500 lines, (b) the body uses pure XML structure with no markdown headings, (c) `<objective>` and `<success_criteria>` tags are present, (d) the description is directive (invoked skill) or `disable-model-invocation: true` with a passive description (reference skill), and (e) the skill passes `/auditing-skills` with no must-fix items.
</success_criteria>

<reference_note>
This is a reference skill. `/creating-skills` and `/auditing-skills` load these standards automatically. Do not invoke directly.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, check for `spx/local/standardizing-skills.md` at the repository root. Read that file after this reference if it exists and apply it as the repo-local specialization (e.g., marketplace-specific naming conventions or additional constraints).
</repo_local_overlay>

---

<skill_organization>

Skills follow a **reference pattern** to avoid duplication:

1. **Foundational skill** (e.g., `/testing`) — core principles and domain-agnostic patterns.
2. **Language-specific skills** (e.g., `/testing-python`, `/testing-typescript`) — reference the foundational skill, provide only language-specific implementations.
3. **Reference skills** (e.g., `/standardizing-typescript`, `/standardizing-skills`) — standards loaded by other skills, never invoked directly.

For language-specific skills that reference a foundation, use unqualified names (`/testing`) so they resolve to whichever foundational skill is installed.

**Skill invocation limitations:** Skills cannot automatically invoke other skills. They can:

1. Instruct the agent to read another skill file first
2. Reference foundational concepts by skill name
3. Be invoked sequentially by the user or agent

</skill_organization>

---

<frontmatter>

Every SKILL.md starts with YAML frontmatter. The fields that appear — and their constraints:

| Field                      | Required | Constraint                                                                                  |
| -------------------------- | -------- | ------------------------------------------------------------------------------------------- |
| `name`                     | Yes      | Lowercase letters, numbers, hyphens. ≤64 chars. Must match directory name.                  |
| `description`              | Yes      | ≤1024 chars. Directive style (see `<descriptions>`). Passive for references.                |
| `allowed-tools`            | No       | Comma-separated list. Restrict for audit (read-only) and reference skills.                  |
| `argument-hint`            | No       | Free-text hint shown at invocation. Use for skills that take a path or identifier argument. |
| `disable-model-invocation` | No       | `true` for reference skills — prevents false activations.                                   |
| `model`                    | No       | Model ID override. Use for complex-reasoning skills that need a stronger model.             |

```yaml
# Invoked skill (routing, workflow, creation)
---
name: creating-skills
description: >-
  ALWAYS invoke this skill when creating, editing, or improving SKILL.md files.
  NEVER create or modify skills without this skill.
---
```

```yaml
# Reference skill (standards, loaded by others)
---
name: standardizing-skills
disable-model-invocation: true
description: >-
  Skill authoring standards enforced across all creating and auditing skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---
```

Audit skills (`auditing-*`) must add `allowed-tools: Read, Grep, Glob, Bash` per the CLAUDE.md read-only rule — audit runs never modify files.

**Directory match is mandatory.** `skills/authoring/` → `name: authoring`. A mismatch breaks skill lookup.

</frontmatter>

---

<naming_conventions>

The `name` field is the user invocation path (`/skill-name`). Match user speech patterns.

**Rules:**

- Use domain acronyms: `authoring` not `authoring-spec-tree-artifacts`
- Use terms users actually say: `testing-python` not `python-unit-test-framework`
- Think "CD-ROM" not "Compact Disc Read Only Memory"
- Directory name MUST match: `skills/authoring/` → `name: authoring`

**Gerund form preferred:** `creating-skills`, `processing-pdfs`, `reviewing-code`.

```yaml
# ✅ Matches user speech
name: authoring # Users say "author a spec"
name: testing-typescript # Users say "test TypeScript code"
name: bootstrapping # Users say "bootstrap the spec tree"

# ❌ Nobody says these
name: authoring-spec-tree-artifacts # Too verbose
name: typescript-testing-framework # Wrong order
```

</naming_conventions>

---

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

**Reference skills** use `disable-model-invocation: true` with a passive description:

```yaml
disable-model-invocation: true
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
```

**Conflict resolution:** If Claude picks the wrong skill, descriptions are too similar. Make trigger terms distinct — "sales data in Excel" vs "log files and system metrics".

</descriptions>

---

<xml_structure>

Skills use **pure XML structure** — no markdown headings (`#`, `##`, `###`) anywhere in the body. Keep markdown formatting *within* content (bold, italic, lists, tables, code blocks, links).

**Why pure XML:** unambiguous section boundaries, consistent cross-skill structure, better token efficiency, better Claude performance.

**Required tags (every skill):**

| Tag                  | Content                                           |
| -------------------- | ------------------------------------------------- |
| `<objective>`        | What the skill does and why it matters.           |
| `<success_criteria>` | How to know the task worked; completion criteria. |

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

**Semantic names:** `<workflow>` not `<steps>`, `<success_criteria>` not `<done>`, `<anti_patterns>` not `<dont_do>`.

**Reference tags in prose by name:** "Using the schema in `<schema>` tags…", "Follow the workflow in `<workflow>`…". Makes structure self-documenting.

**Intelligence rules** — match structure to complexity:

| Skill class                               | Expected tags                                                                   |
| ----------------------------------------- | ------------------------------------------------------------------------------- |
| Simple (single domain)                    | `<objective>`, `<success_criteria>`, optionally `<quick_start>`                 |
| Medium (multiple patterns)                | Required + `<workflow>` and/or `<examples>`                                     |
| Complex (multi-domain, API, sec)          | Required + router pattern + appropriate conditional tags                        |
| Foundation / gate / validator / reference | Required + `<workflow>`. **Omit** `<quick_start>` — no abbreviated path exists. |

Don't over-engineer simple skills. Don't under-specify complex ones.

</xml_structure>

---

<progressive_disclosure>

SKILL.md is an overview. Reference files carry detail. Claude loads reference files only when needed.

**Rules:**

- Keep SKILL.md under 500 lines.
- References live in `references/` one level deep from SKILL.md. Do not nest references that read other references — Claude may only partially read transitive files.
- Reference files over 100 lines need a table of contents at the top, so partial reads still see the full scope.
- Use forward slashes in every path — `references/guide.md`, never `references\guide.md`. Works across platforms.

**Token efficiency:** simple task loads SKILL.md only (~500 tokens); medium loads SKILL.md + one reference (~1000); complex loads SKILL.md + multiple (~2000+).

```text
✅ One level deep
SKILL.md → references/advanced.md (complete info)
         → references/examples.md (complete info)

❌ Nested
SKILL.md → references/advanced.md → references/details.md → actual info
```

**Name reference files descriptively** — `xml-structure-examples.md`, not `examples.md`. The filename is also a table-of-contents entry in `<reference_index>`.

</progressive_disclosure>

---

<conciseness>

The context window is shared. A skill competes for tokens with the system prompt, conversation history, other skills' metadata, and the user's request.

**Test every sentence:** "Does removing this reduce Claude's effectiveness at the task?" If no — cut it.

**What Claude already knows (never include):**

- General programming knowledge
- Language syntax and standard-library APIs
- Common design patterns
- How to use its own tools

**What Claude needs (include):**

- Project-specific conventions that contradict common patterns
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

---

<skill_types>

Six skill types. Each has a distinct purpose and primary output.

| Type           | Purpose                      | Primary output                    | Key sections                                                                   |
| -------------- | ---------------------------- | --------------------------------- | ------------------------------------------------------------------------------ |
| **Builder**    | Create new artifacts         | Code, documents, widgets, configs | Required clarifications, output spec, domain standards, templates in `assets/` |
| **Guide**      | Teach procedures             | Step-by-step workflows, tutorials | Numbered workflow, input→output example pairs, decision trees                  |
| **Automation** | Execute multi-step processes | Processed files, transformed data | Tested scripts in `scripts/`, error handling, dependencies, I/O contracts      |
| **Analyzer**   | Extract insights             | Reports, summaries, reviews       | Analysis scope, evaluation criteria, output format, synthesis                  |
| **Validator**  | Enforce quality              | Pass/fail verdicts, scores        | Criteria with thresholds, scoring rubric, remediation guidance                 |
| **Reference**  | Share domain knowledge       | Standards loaded by other skills  | `disable-model-invocation: true`, passive description, `allowed-tools: Read`   |

**Type-selection rule of thumb:**

- Creates new artifacts → Builder
- Teaches how-to → Guide
- Executes processes → Automation
- Extracts insights → Analyzer
- Checks quality → Validator
- Shares knowledge multiple skills need → Reference

</skill_types>

---

<reference_skills>

Reference skills hold shared domain knowledge that multiple skills need. They are **not** invoked directly — consuming skills reach them via `/skill-name` references in their text.

**When to create a reference skill.** Two or more skills in the same plugin need the same domain knowledge (standards, patterns, anti-patterns, conventions). Alternatives fail: duplicating the content creates maintenance drift, and putting it in one skill's `references/` directory makes it unreachable from the other skill's `${CLAUDE_SKILL_DIR}`.

**Required frontmatter:**

```yaml
---
name: standardizing-{domain}
disable-model-invocation: true
description: >-
  {Domain} standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---
```

- `disable-model-invocation: true` — prevents false activations from user prompts.
- Passive description (no `ALWAYS`/`NEVER`) — directive descriptions trigger false activations for a reference.
- `allowed-tools: Read` — reference skills only read.

**How consuming skills reference it.** Write `/standardizing-X` in running text; Claude loads the reference into context on encounter.

```markdown
# In writing-prose/SKILL.md:

Zero tolerance for patterns in `/standardizing-prose` — never use any of them.

# In reviewing-prose/SKILL.md:

Before reviewing, read `/standardizing-prose` for the complete catalog of anti-patterns.
```

**Naming convention:** `standardizing-{domain}` for standards. Examples: `standardizing-python`, `standardizing-typescript-tests`, `standardizing-prose`, `standardizing-skills`.

**Extraction completeness test.** When factoring a `standardizing-*` reference out of a builder/auditor pair, the extraction is complete only when the corresponding `auditing-*` skill loads the new reference and nothing else for standards. If the auditor still reads files from the builder's `references/` directory for standards, content is still stranded there — finish the move. The same rule catches partial extractions: a standards file in `creating-X/references/` that the auditor needs is a bug, not an architecture.

**Anti-patterns:**

- Directive descriptions (`ALWAYS`/`NEVER`) — cause false activations.
- Shared content buried in one skill's `references/` — `${CLAUDE_SKILL_DIR}` is isolated per skill.
- Same content duplicated across multiple `references/` — drifts.
- Partial extraction: naming a new `standardizing-*` skill while leaving the meat in the builder's `references/` — the auditor keeps reading the old location and the rename becomes a lie.

</reference_skills>

---

<templates_and_variables>

**Referencing skill files from SKILL.md:**

Use `${CLAUDE_SKILL_DIR}` to reference files within a skill. Claude Code expands it to the absolute path of the skill's directory before the agent sees the content.

```markdown
Read `${CLAUDE_SKILL_DIR}/references/example.md`
```

Do NOT define aliases, add troubleshooting sections, or explain what the variable is. The agent sees an absolute path, not the variable.

**Variable scopes:**

| Variable                | Scope                      | Skill content (`!` commands) | Hook `command:` field |
| ----------------------- | -------------------------- | ---------------------------- | --------------------- |
| `${CLAUDE_SKILL_DIR}`   | Skill's SKILL.md directory | Yes                          | **No**                |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin installation root   | No                           | **Yes**               |
| `${CLAUDE_PLUGIN_DATA}` | Plugin persistent data dir | No                           | **Yes**               |
| `$CLAUDE_PROJECT_DIR`   | Project working directory  | No                           | **Yes**               |

For hook scripts bundled with a plugin skill, use `${CLAUDE_PLUGIN_ROOT}`:

```yaml
hooks:
  PostToolUse:
    - matcher: "Skill"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/skills/my-skill/scripts/hook.sh"
```

</templates_and_variables>

---

<platform_constraints>

Two platform footguns affect skill authoring: dprint's `markup_fmt` handling of nested code fences, and Claude Code's bash-safety checker for `!` expansion. Read `${CLAUDE_SKILL_DIR}/references/platform-constraints.md` before using multi-backtick fences or `!` command syntax.

</platform_constraints>

---

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

Enforced by the `fix-xml-spacing` pre-commit hook (`scripts/fix-xml-spacing.py`).

</xml_tag_formatting>

---

<validation_rule>

Validation scripts catch errors Claude might miss. They are force multipliers for quality-critical skills.

**A good validation script:**

- Emits verbose, specific error messages.
- Shows available valid options when something is invalid.
- Pinpoints the exact location of the problem.
- Suggests an actionable fix.
- Is deterministic — same input, same output.

```text
❌ "Validation failed."
✅ "Field 'signature_date' not found.
    Available fields: customer_name, order_total, signature_date_signed
    Did you mean 'signature_date_signed'?"
```

Verbose errors let Claude fix issues without user intervention.

</validation_rule>

---

<script_testing_rule>

Scripts shipped in a skill's `scripts/` directory must be tested before inclusion. The skill's documentation should record what was tested and with what inputs:

```bash
# scripts/extract_text.py
# Tested with:
# - Single page PDF ✓
# - Multi-page PDF ✓
# - Scanned PDF (OCR) ✓
# - Encrypted PDF → Returns clear error ✓
# - Non-PDF file → Returns clear error ✓
```

Cover: sample input, expected output match, error cases (invalid input, missing files), and cleanup (no temp files left behind).

</script_testing_rule>

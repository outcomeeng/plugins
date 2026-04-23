---
name: standardizing-skills
disable-model-invocation: true
description: >-
  Skill authoring standards enforced across all creating and auditing skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical standards for skill authoring: naming conventions, description wording, organizational patterns, template variables, and Claude Code-specific constraints. Defines what /creating-skills must follow and /auditing-skills enforces.
</objective>

<success_criteria>
Skills conform to these standards when they pass /auditing-skills with no must-fix items and achieve reliable activation.
</success_criteria>

<reference_note>
This is a reference skill. /creating-skills and /auditing-skills load these standards automatically. Do not invoke directly.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, check for `spx/local/standardizing-skills.md` at the repository root. Read that file after this reference if it exists and apply it as the repo-local specialization (e.g., marketplace-specific naming conventions or additional constraints).
</repo_local_overlay>

---

<skill_organization>

Skills follow a **reference pattern** to avoid duplication:

1. **Foundational skill** (e.g., `/testing`) — Contains core principles and domain-agnostic patterns
2. **Language-specific skills** (e.g., `/testing-python`, `/testing-typescript`) — Reference the foundational skill, provide only language-specific implementations
3. **Reference skills** (e.g., `/standardizing-typescript`) — Standards loaded by other skills, never invoked directly

For language-specific skills that reference a foundation, use unqualified names (`/testing`) so they resolve to whichever foundational skill is installed.

**Skill invocation limitations:** Skills cannot automatically invoke other skills. They can:

1. Instruct the agent to read another skill file first
2. Reference foundational concepts by skill name
3. Be invoked sequentially by the user or agent

</skill_organization>

---

<naming_conventions>

The `name` field in SKILL.md YAML frontmatter is the user invocation path (`/skill-name`). Match user speech patterns.

**Rules:**

- Use domain acronyms: `authoring` not `authoring-spec-tree-artifacts`
- Use terms users actually say: `testing-python` not `python-unit-test-framework`
- Think "CD-ROM" not "Compact Disc Read Only Memory"
- Directory name MUST match: `skills/authoring/` → `name: authoring`

**Gerund form preferred:** `creating-skills`, `processing-pdfs`, `reviewing-code`

```yaml
# ✅ Good: matches user speech
name: authoring # Users say "author a spec"
name: testing-typescript # Users say "test TypeScript code"
name: bootstrapping # Users say "bootstrap the spec tree"

# ❌ Bad: nobody says these
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

**Use directive descriptions:**

```yaml
description: >-
  ALWAYS invoke this skill when <triggers>.
```

**NEVER constraint — add only when it disambiguates:**

Add NEVER when:

- The skill is the only one with that negative (e.g., `NEVER work on the spec tree without loading context` — only contextualizing says this)
- Claude has a strong built-in alternative the NEVER prevents (e.g., `NEVER run git commit without this skill` — Claude would just run `git commit` directly)

Omit NEVER when:

- Multiple skills share the same negative (adds noise, doesn't help routing)
- The ALWAYS trigger is already specific enough

**For language-specific skills, put the language after the artifact:**

```yaml
# ✅ Matches user speech: "audit ADRs for Python"
ALWAYS invoke this skill when auditing ADRs for Python.

# ❌ Unnatural phrasing
ALWAYS invoke this skill when auditing Python ADRs.
```

**Reference skills** (loaded by other skills, not invoked directly):

```yaml
disable-model-invocation: true
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
```

**Match user speech over formal jargon:** Use abbreviations users would use (ADR not Architecture Decision Record). Avoid corporate speak.

**Conflict resolution:** If Claude picks the wrong skill, descriptions are too similar. Make trigger terms distinct — "sales data in Excel" vs "log files and system metrics".

</descriptions>

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

**Nested code fences (MANDATORY):** Never nest multiple 3-backtick blocks inside a single 4-backtick fence. `markup_fmt` (dprint) prematurely closes the outer fence after the first inner fence, breaking all subsequent content.

Workaround: move examples that need nested code fences into `references/` files and reference them from SKILL.md:

```markdown
<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-review.md` for a complete example.
</example_review>
```

A single inner code block inside a 4-backtick fence is fine. The problem occurs with multiple inner blocks.

**XML tag formatting (MANDATORY):** Always add a blank line before closing pseudo-XML tags that follow unordered lists. Without it, markdown parsers indent the closing tag as part of the last list item.

```markdown
# ❌ WRONG

- Item 1
- Item 2

</section>

# ✅ CORRECT

- Item 1
- Item 2

</section>
```

This formatting is automatically enforced by the `fix-xml-spacing` pre-commit hook (`scripts/fix-xml-spacing.py`).

</templates_and_variables>

---

<bash_expansion_restrictions>

`!` bash expansion in skill commands has restrictions. Use single quotes for outer strings when inner strings contain double quotes:

```bash
# ✅ Single quotes outside, double quotes inside
!`spx session list || echo 'Ask user to install: "npm install --global @outcomeeng/spx"'`

# ❌ Triggers "ambiguous syntax" permission error
!`spx session list || echo "Ask user to install: \"npm install --global @outcomeeng/spx\""`
```

**Avoid in `!` commands:**

- Shell operators: `(N)` nullglob, `*` globbing in zsh
- Parameter substitution: `${f/DOING/TODO}`
- Loops: `while read f; do ... done`
- Complex awk/sed pipelines with nested quotes

These all trigger permission errors from the Claude Code bash safety checker.

</bash_expansion_restrictions>

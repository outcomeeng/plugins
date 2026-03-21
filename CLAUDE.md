# Outcome Engineering Plugin Marketplace

Claude Code plugin marketplace (`outcomeeng/claude`) for spec-driven development with [Outcome Engineering](https://outcome.engineering) and [SPX](https://spx.sh).

## Marketplace Is a Product

We develop the "features" of this marketplace like a software product. We are currently starting out from scratch, so there is not yet much to be found, but as we progress, everything will be in `spx/` (specs as durable map).

## Always use `AskUserQuestion` Tool

**Always use the `AskUserQuestion` tool to obtain guidance from the user, such as: discover context, obtain rationale, as well as to support the user in makking the right call by asking critical questions before blindly following the user's requests**

**NEVER ask the user any questions without using the `AskUserQuestion` tool**

## Markdown Formatting Rules

**IMPORTANT: Pseudo-XML in Markdown Code Fences**

When documenting XML-like syntax that isn't valid XML (pseudo-XML with text content, no proper elements), **ALWAYS use `text` as the language identifier**, not `xml`:

```text
<!-- ✅ CORRECT: Use "text" for pseudo-XML -->
<metadata>
  timestamp: [UTC timestamp]
  project: [Project name]
</metadata>
```

**Why:** The markup formatter (`markup_fmt`) in dprint will attempt to format XML code fences and can mangle pseudo-XML syntax. Using `text` prevents this issue while maintaining syntax highlighting compatibility with most linters.

**Never use:**

- `` ```xml `` for pseudo-XML (causes formatting issues)
- `` ``` `` with no language identifier (rejected by some markdown linters)

## Documentation

### Official Anthropic Resources

**Core Documentation:**

- [Create plugins](https://code.claude.com/docs/en/plugins) - How to create and structure plugins
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) - How to create and distribute marketplaces
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference) - Complete technical specifications, schemas, and CLI commands
- [Discover Plugins](https://code.claude.com/docs/en/discover-plugins) - How users find and install plugins
- [Agent Skills](https://code.claude.com/docs/en/skills) - Creating and using Skills

**Announcements:**

- [Claude Code Plugins Announcement](https://www.anthropic.com/news/claude-code-plugins) - Official plugin system launch
- [Agent Skills Introduction](https://www.anthropic.com/news/skills) - Skills feature announcement

**Best Practices:**

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) - Agentic coding patterns

## Version Management

### Versioning Rules (Conservative Approach)

All plugins follow semantic versioning: `MAJOR.MINOR.PATCH`

**MAJOR version (0.x.x → 1.x.x):**

- ⛔ **NEVER bump unless user explicitly requests it**
- All plugins remain at major version `0` until stable release
- Reserved for future stable release when all features are production-ready

**MINOR version (0.3.x → 0.4.x):**

- ✅ Adding new commands (e.g., new `/pickup` command)
- ✅ Adding new skills (e.g., new `/designing-frontend` skill)
- ✅ Major functional changes (e.g., atomic claim mechanism in `/pickup`)
- ✅ Significant user experience improvements
- 🎯 **Use sparingly** - only for substantial additions or changes

**PATCH version (0.3.1 → 0.3.2):**

- ✅ **Most common** - default for most changes
- ✅ Bug fixes
- ✅ Refactoring existing code
- ✅ Documentation improvements
- ✅ Small enhancements to existing features
- ✅ Performance optimizations
- ✅ Internal implementation changes
- 🎯 **Use liberally** - when in doubt, use PATCH

### Files to Update When Bumping Version

**Plugin version** (always update):

```bash
plugins/{plugin-name}/.claude-plugin/plugin.json
```

```json
{
  "name": "claude",
  "version": "0.4.0" // ← Update this
}
```

**Marketplace catalog** (optional, only if description changes):

```bash
.claude-plugin/marketplace.json
```

```json
{
  "plugins": [
    {
      "name": "claude",
      "source": "./plugins/claude",
      "description": "..." // ← Only update if description changes
    }
  ]
}
```

**IMPORTANT:** Validate after any changes:

```bash
# Validate marketplace.json
claude plugin validate .

# Validate plugin.json
find plugins -maxdepth 1 -type d -mindepth 1 -exec claude plugin validate {} \;
```

### Version Bump Workflow

**CRITICAL: Version bumps must be in the SAME commit as the changes that warrant them.**

❌ **WRONG** - Separate commits:

```bash
git commit -m "refactor(skills): simplify descriptions"
# ... then later ...
git commit -m "chore: bump versions"
```

✅ **CORRECT** - Single atomic commit:

```bash
# 1. Make your changes to skills/commands/etc
# 2. Update version numbers in plugin.json files
# 3. Stage everything together
git add plugins/*/skills/ plugins/*/.claude-plugin/plugin.json
# 4. Create ONE commit with both the changes and version bumps
git commit -m "refactor(skills): simplify descriptions

- Simplified skill descriptions from formal jargon to natural language
- All plugins: patch version bump (descriptions improved)"
```

**Rationale:** The version number is metadata about the changes, not a separate logical change. Splitting them creates awkward history where commits have changes but outdated version numbers.

**Exception:** Only create a separate version bump commit if you're bumping versions WITHOUT any code/doc changes (rare).

### Version Bump Examples

| Change                      | Old   | New   | Reason                          |
| --------------------------- | ----- | ----- | ------------------------------- |
| Add `/handoff` command      | 0.2.0 | 0.3.0 | New command = MINOR             |
| Add self-organizing handoff | 0.3.0 | 0.4.0 | Major functional change = MINOR |
| Fix typo in handoff.md      | 0.4.0 | 0.4.1 | Documentation fix = PATCH       |
| Refactor pickup logic       | 0.4.1 | 0.4.2 | Refactoring = PATCH             |
| Improve error messages      | 0.4.2 | 0.4.3 | Small enhancement = PATCH       |
| Add `/designing-frontend`   | 0.4.3 | 0.5.0 | New skill = MINOR               |

## Skill Organization Principles

### Foundational + Language-Specific Pattern

Skills follow a **reference pattern** to avoid duplication:

1. **Foundational skill** (`/testing`) - Contains core principles, methodology, and language-agnostic patterns
2. **Language-specific skills** (`/testing-python`, `/testing-typescript`) - Reference the foundational skill, provide only language-specific implementations

**Usage:** Always read the foundational skill first, then the language-specific skill for concrete patterns.

### Why This Pattern?

- **Single source of truth** - Core principles live in one place
- **No drift** - Changes to methodology propagate automatically
- **Focused content** - Each skill contains only what's unique to it
- **Maintainability** - Less duplication means less divergence over time

### Skill Invocation

Claude Code skills cannot automatically invoke other skills. However, skills can:

1. Instruct Claude to read another skill file first
2. Reference foundational concepts by skill name
3. Be invoked sequentially by the user/Claude

---

## Claude Plugin

Meta-skills for Claude Code plugin development: creating and auditing skills, commands, and subagents.

### Skills

| Skill                 | Purpose                                    |
| --------------------- | ------------------------------------------ |
| `/creating-skills`    | Create and refine Claude Code skills       |
| `/creating-commands`  | Create slash commands with XML structure   |
| `/creating-subagents` | Create and configure subagents             |
| `/auditing-skills`    | Audit skills for best practices compliance |
| `/auditing-commands`  | Audit slash commands for best practices    |
| `/auditing-subagents` | Audit subagent configurations              |

## Core Plugin

Productivity skills and commands.

### Skills

| Skill                 | Purpose                                   |
| --------------------- | ----------------------------------------- |
| `/committing-changes` | Comprehensive git commit message guidance |

### Commands

| Command    | Purpose                                             |
| ---------- | --------------------------------------------------- |
| `/commit`  | Git commit with Conventional Commits (auto-context) |
| `/handoff` | Create timestamped context handoff                  |
| `/pickup`  | Load and continue from previous handoff             |

## Code Plugin

Autonomous coding orchestration.

### Skills

| Skill                  | Purpose                            |
| ---------------------- | ---------------------------------- |
| `/coding-autonomously` | Autonomous implementation patterns |

## Frontend Plugin

Frontend design and coding skills and commands.

### Skills

| Skill                | Purpose                                                  |
| -------------------- | -------------------------------------------------------- |
| `designing-frontend` | Create distinctive, production-grade frontend interfaces |

## Prose Plugin

Prose craft skills for writing and reviewing.

### Skills

| Skill              | Purpose                                                   |
| ------------------ | --------------------------------------------------------- |
| `/writing-prose`   | Write varied, specific, human prose (always active)       |
| `/reviewing-prose` | Review and edit prose for formulaic patterns (on request) |

## Test Plugin (`/testing`)

The test plugin provides BDD testing methodology with three-level testing:

| Level          | Question                               | Requirements                     |
| -------------- | -------------------------------------- | -------------------------------- |
| 1: Unit        | "Is our logic correct?"                | Dependency injection, NO mocking |
| 2: Integration | "Does it work with real dependencies?" | Documented test harnesses        |
| 3: E2E         | "Does it work for users?"              | Documented credentials           |

### Skills

| Skill              | Purpose                                                       |
| ------------------ | ------------------------------------------------------------- |
| `/testing`         | Foundational testing methodology (5 stages, 5 factors)        |
| `/reviewing-tests` | Foundational test review protocol (loaded by language skills) |

**Core rules:**

- No mocking - use dependency injection at Level 1, real dependencies at Level 2+
- Tests co-located with specs in `spx/.../tests/` with suffix naming (`*.unit.test.ts`)
- Test level in filename: `*.unit.test.ts`, `*.integration.test.ts`, `*.e2e.test.ts`

## TypeScript Plugin

Complete TypeScript development workflow with testing, implementation, and review.

### Skills

| Skill                                | Purpose                                                    |
| ------------------------------------ | ---------------------------------------------------------- |
| `/testing-typescript`                | TypeScript-specific testing patterns (requires `/testing`) |
| `/coding-typescript`                 | Implementation workhorse with remediation loop             |
| `/reviewing-typescript`              | Strict code review with zero-tolerance                     |
| `/reviewing-typescript-tests`        | TypeScript test review (requires `/reviewing-tests`)       |
| `/architecting-typescript`           | ADR producer with testing strategy                         |
| `/reviewing-typescript-architecture` | ADR validator against testing principles                   |
| `/orchestrating-typescript`          | Orchestrate story implementation through skills            |

### Commands

| Command            | Purpose                                     |
| ------------------ | ------------------------------------------- |
| `/auto-typescript` | Implement stories in a feature sequentially |

### Core Principles

- No mocking - dependency injection only
- Reality is the oracle
- Behavior testing, not implementation testing
- Tests at appropriate levels (Unit/Integration/E2E)
- Pure XML structure in all skills
- Self-contained skills (no inter-skill invocations)

## Python Plugin

Complete Python development workflow with testing, implementation, and review.

### Skills

| Skill                            | Purpose                                                |
| -------------------------------- | ------------------------------------------------------ |
| `/testing-python`                | Python-specific testing patterns (requires `/testing`) |
| `/coding-python`                 | Implementation workhorse with remediation loop         |
| `/reviewing-python`              | Strict code review with zero-tolerance                 |
| `/reviewing-python-tests`        | Python test review (requires `/reviewing-tests`)       |
| `/architecting-python`           | ADR producer with testing strategy                     |
| `/reviewing-python-architecture` | ADR validator against testing principles               |
| `/orchestrating-python`          | Orchestrate story implementation through skills        |

### Commands

| Command        | Purpose                                     |
| -------------- | ------------------------------------------- |
| `/auto-python` | Implement stories in a feature sequentially |

### Core Principles

- No mocking - dependency injection only
- Reality is the oracle
- Behavior testing, not implementation testing
- Tests at appropriate levels (Unit/Integration/E2E)

## Spec Tree Plugin

Spec-driven development with the Spec Tree framework. Supersedes `spx-legacy`.

### Skills

| Skill              | Purpose                                       |
| ------------------ | --------------------------------------------- |
| `/understanding`   | Foundation skill — loaded before any other    |
| `/contextualizing` | Show status, progress, what exists            |
| `/authoring`       | Add, define, create specs and features        |
| `/decomposing`     | Break down, split, scope work                 |
| `/refactoring`     | Move nodes, re-scope, extract shared enablers |
| `/aligning`        | Review, check consistency, audit, find gaps   |
| `/testing`         | Create tests, run tests, check stale status   |

## SPX Plugin

Commands for spec-driven development projects.

### Skills

| Skill                 | Purpose                                   |
| --------------------- | ----------------------------------------- |
| `/committing-changes` | Comprehensive git commit message guidance |

### Commands

| Command    | Purpose                                                    |
| ---------- | ---------------------------------------------------------- |
| `/commit`  | Git commit with Conventional Commits (auto-context)        |
| `/handoff` | Create timestamped context handoff                         |
| `/pickup`  | Load and continue from previous handoff                    |
| `/rtfm`    | Load specs and testing methodology before writing any code |
| `/clarify` | Clarify ambiguous requirements                             |

## SPX-Legacy Plugin (Deprecated)

**Deprecated — superseded by Spec Tree plugin.** Legacy Outcome Engineering (spx/) skills for projects that haven't migrated.

### Skills

| Skill                    | Purpose                                           |
| ------------------------ | ------------------------------------------------- |
| `/writing-prd`           | Write PRDs documenting what users need and why    |
| `/managing-spx`          | Create and manage spx/ specs                      |
| `/understanding-spx`     | Read all specs before starting work               |
| `/decomposing-*`         | Decompose PRDs to capabilities, features, stories |
| `/migrating-spec-to-spx` | Migrate from specs/ to spx/ format                |

## Specs Plugin (Legacy)

Legacy `specs/` directory support. Use for projects that haven't migrated.

### Skills

| Skill                  | Purpose                                    |
| ---------------------- | ------------------------------------------ |
| `/managing-specs`      | Create and manage specs structure and ADRs |
| `/understanding-specs` | Load context before implementation         |

### Disambiguation: specs/ vs spx/ vs Spec Tree

| Directory | System                           | Plugin       |
| --------- | -------------------------------- | ------------ |
| `specs/`  | Legacy                           | `specs`      |
| `spx/`    | Outcome Engineering (deprecated) | `spx-legacy` |
| `spx/`    | Spec Tree (current)              | `spec-tree`  |

If unclear which system to use, ask the user.

## Discovering Other Installed Skills

Search for `SKILL.md` in `.claude/plugins/cache/{marketplace-name}/{plugin-name}/`

## Proactive Skill Invocation

Certain skills must be invoked **automatically** when specific conditions are met, without waiting for explicit user request.

### Step 1: Determine Which System

**FIRST**, check which directory exists:

| Directory | System                           | Use Skills From |
| --------- | -------------------------------- | --------------- |
| `spx/`    | Spec Tree (current)              | `spec-tree`     |
| `spx/`    | Outcome Engineering (deprecated) | `spx-legacy`    |
| `specs/`  | Legacy                           | `specs`         |

If unclear which system, ask the user. Prefer Spec Tree if `spec-tree` plugin is installed.

### Step 2: Invoke the Appropriate Skills

**BEFORE implementing any work item** (capability/feature/story), you MUST:

1. **Invoke understanding/contextualizing skill** on the work item file
   - **Spec Tree**: `/spec-tree:contextualizing` | **SPX-Legacy**: `/spx-legacy:understanding-spx` | **Legacy**: `/specs:understanding-specs`
   - **Trigger**: User requests implementation of a work item
   - **Purpose**: Load complete context hierarchy (requirements → decisions → work item)
   - **Example**: User says "implement story-21" → STOP and invoke understanding skill FIRST
   - **Non-negotiable**: Do NOT read story/feature/capability files directly without invoking this skill

2. **Invoke authoring/managing skill** when creating specs or work items
   - **Spec Tree**: `/spec-tree:authoring` | **SPX-Legacy**: `/spx-legacy:managing-spx` | **Legacy**: `/specs:managing-specs`
   - **Trigger**: User requests creating capability, feature, story, PRD, or ADR
   - **Purpose**: Access templates from skill's `templates/` directory, understand numbering
   - **Example**: User says "create the feature" → STOP and invoke authoring skill to read template
   - **Critical**: Templates are in `.claude/plugins/cache/.../templates/`, NOT in the project

**Pattern**: These skills are preparatory and blocking. You MUST invoke them BEFORE writing code or documents.

**Rationale**: Without these skills, you will:

- Miss requirements and violate ADRs
- Search for templates that don't exist in the project
- Create work items with incorrect numbering
- Generate requirements documents with wrong structure

## Naming Skills

The `name` field in SKILL.md YAML frontmatter is how users invoke your skill (`/skill-name`).

**Match user speech patterns:**

- Use domain acronyms: `writing-prd` not `writing-prd-document`
- Use terms users actually say: `testing-python` not `python-unit-test-framework`
- Think "CD-ROM" not "Compact Disc Read Only Memory"

**Directory name must match:**

- Directory: `skills/writing-prd/`
- YAML name: `name: writing-prd`
- User invokes: `/writing-prd`

**Examples from this marketplace:**

```yaml
# ✅ Good: matches user speech
name: writing-prd
# Users say "write a PRD"

name: testing-typescript
# Users say "test TypeScript code"

name: autopython
# Users say "autopython" (command name)
```

```yaml
# ❌ Bad: nobody says these
name: writing-prd-document
# Too verbose, doesn't match speech

name: typescript-testing-framework
# Wrong order, unnatural phrasing
```

## Writing effective descriptions

The description field enables Skill discovery and should include both what the Skill does and when to use it. The description is critical for skill selection: Claude uses it to choose the right Skill from potentially 100+ available Skills. The description must provide enough detail for Claude to know when to select this Skill, while the rest of SKILL.md provides the implementation details.

**Keep descriptions concise** - Claude has a character budget for all skill metadata (name, args, description). When the budget is exceeded, Claude sees only a subset of available skills, making some skills invisible.

### Directive descriptions for reliable activation

Research (Seleznov, 650 automated trials, Feb 2026) shows description wording has a **20x impact on activation odds**:

| Style         | Activation | Example                                         |
| ------------- | ---------- | ----------------------------------------------- |
| Passive       | ~77%       | `Docker expert for containerization. Use when…` |
| Expanded      | ~93%       | `…or any Docker-related task`                   |
| **Directive** | **~100%**  | `ALWAYS invoke… Do not X directly`              |

**Use directive descriptions with negative constraints.** The recommended template:

```yaml
description: >-
  ALWAYS invoke this skill when <triggers>.
  NEVER <alternative action> without this skill.
```

The negative constraint is load-bearing. Skills where Claude has strong built-in alternatives (file operations, git, code review) benefit most from this pattern.

**Keep negatives language-agnostic.** Write `NEVER review code without this skill`, not `Do not review Python code directly`. The agent knows which language is in play, and typically only one language-specific skill is installed per project.

See [research/skill-invocation.md](research/skill-invocation.md) for the full study and additional strategies.

### Additional description guidelines

**Match actual user speech, not formal jargon.** Use the exact words and phrases users say, avoiding technical or formal language. Use abbreviations if the user would (ADR not Architecture Decision Record). Avoid corporate speak ("hierarchical context ingestion protocol" → "read all specs").

**Multiple Skills conflict:**

If Claude uses the wrong Skill or seems confused between similar Skills, the descriptions are probably too similar. Make each description distinct by using specific trigger terms.

For example, instead of two Skills with "data analysis" in both descriptions, differentiate them: one for "sales data in Excel files and CRM exports" and another for "log files and system metrics". The more specific your trigger terms, the easier it is for Claude to match the right Skill to your request.

### Reference skills

Skills that exist only to be loaded by other skills (e.g., `standardizing-python`) should NOT use directive descriptions — that would cause false activations. Instead, use `disable-model-invocation: true` and a passive description:

```yaml
disable-model-invocation: true
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
```

### Effective examples

**PDF Processing skill:**

```yaml
description: >-
  ALWAYS invoke this skill when working with PDF files, extracting text, filling forms, or merging documents.
  NEVER process PDFs without this skill.
```

**Git Commit Helper skill:**

```yaml
description: >-
  ALWAYS invoke this skill when writing commit messages or reviewing staged changes.
  NEVER run git commit without this skill.
```

### Examples from this marketplace

**SPX Plugin skills (differentiating similar skills):**

```yaml
# ✅ Good: directive with negative constraint
name: writing-prd
description: >-
  ALWAYS invoke this skill when writing PRDs or product requirements.
  NEVER write PRDs without this skill.

name: managing-spx
description: >-
  ALWAYS invoke this skill when creating or organizing specs, capabilities, features, stories, or ADRs.
  NEVER create, read, or modify any files in the spx/ directory without this skill.

name: understanding-spx
description: >-
  ALWAYS invoke this skill before implementing any work item to load complete context.
  NEVER create, read, or modify any files in the spx/ directory without this skill.
```

**Why these work:**

- `ALWAYS` tells Claude when to activate (specific triggers)
- `NEVER` tells Claude what NOT to do without the skill (negative constraint)
- Natural language users actually say ("writing PRDs" not "PRD creation protocol")
- Short and direct

```yaml
# ❌ Bad: passive style (77% activation)
name: understanding-specs
description: Read all specs for a story before starting work. Use when starting implementation.
# Problem: Claude will just read the files directly instead of invoking the skill

# ❌ Bad: formal jargon
name: writing-prd
description: Systematic PRD creation with user value propositions and measurable outcomes.
# Problem: Nobody says "user value propositions"
```

**Testing Plugin skills (language-specific differentiation):**

```yaml
# ✅ Good: language in trigger, generic negative
name: testing-python
description: >-
  ALWAYS invoke this skill when writing Python tests or fixing test failures.
  NEVER write tests without this skill.

name: testing-typescript
description: >-
  ALWAYS invoke this skill when writing TypeScript tests or fixing test failures.
  NEVER write tests without this skill.
```

**Why these work:**

- Language in the trigger differentiates (Python vs TypeScript)
- Negative is language-agnostic — the agent knows which language is in play
- Trigger includes both writing AND fixing (covers the full lifecycle)

---

## Writing Skills with Templates

### Template Access Pattern (MANDATORY)

**When a skill includes templates in subdirectories, always use the `${SKILL_DIR}` variable pattern to make template locations unambiguous.**

Skills are loaded from the skill's base directory (`.claude/plugins/cache/{marketplace}/{plugin}/{version}/skills/{skill-name}/`), NOT from the user's project directory. Agents frequently guess wrong and search in the project directory instead.

#### Required Pattern

```markdown
<accessing_templates>

## How to Access Templates

**All templates are stored within this skill's base directory.**

### Understanding Skill Directory Structure

When you invoke `/{skill-name}`, Claude loads this skill from the skill's base directory. Throughout this documentation, we refer to this as `${SKILL_DIR}`.

**The skill's base directory path pattern:**

\`\`\`
.claude/plugins/cache/{marketplace-name}/{plugin-name}/{version}/skills/{skill-name}/
\`\`\`

### Template Organization

All templates are under `${SKILL_DIR}/templates/`:

\`\`\`
${SKILL_DIR}/
├── SKILL.md # This file
└── templates/
└── {template-file}.md
\`\`\`

### How to Read Templates

**Always use the skill's base directory, not the user's project directory.**

\`\`\`zsh

# Pattern

Read: ${SKILL_DIR}/templates/{template-name}

# Example: Read specific template

Read: ${SKILL_DIR}/templates/example.md
\`\`\`

### Troubleshooting

If you cannot find a template:

1. ✅ Verify you're using the skill's base directory, NOT the project directory
2. ✅ Ensure path starts with `${SKILL_DIR}/templates/...`
3. ✅ Use Glob to discover: `Glob: .claude/plugins/cache/**/{skill-name}/templates/**/*.md`
4. ❌ Do NOT look for templates in the user's project

</accessing_templates>
```

#### Update All Template References

Replace all relative paths with `${SKILL_DIR}` prefix:

```bash
# ❌ WRONG - Ambiguous
Read: templates/example.md

# ✅ CORRECT - Unambiguous
Read: ${SKILL_DIR}/templates/example.md
```

### XML Tag Formatting (MANDATORY)

**Always add a blank line before closing pseudo-XML tags that follow unordered lists.**

Without the blank line, markdown parsers interpret the closing tag as part of the list item, causing incorrect indentation.

```markdown
# ❌ WRONG - Tag gets indented as part of list

- Item 1
- Item 2
- Item 3

</section>

# ✅ CORRECT - Blank line prevents indentation

- Item 1
- Item 2
- Item 3

</section>
```

This applies to all pseudo-XML tags used in skills:

- `</objective>`
- `</quick_start>`
- `</structure_definition>`
- `</accessing_templates>`
- `</adr_templates>`
- `</requirement_templates>`
- `</work_item_templates>`
- `</success_criteria>`

**Automated Enforcement:**

This formatting rule is automatically enforced by the `fix-xml-spacing` pre-commit hook:

- **Script**: `scripts/fix-xml-spacing.py`
- **When**: Runs on every commit before other formatters (priority 0)
- **What**: Detects list items followed by closing XML tags, adds blank line, removes indentation
- **Scope**: All `*.md` files in staged changes
- **Behavior**: Automatically stages fixed files

The script respects code fences and won't modify content inside `` ``` `` blocks.

---

## Restrictions on Using `!` Expansion in Commands

```bash
# Avoid shell operators such as `(N)` (nullglob in zsh)
Error: Bash command permission check failed for pattern "!ls .spx/sessions/TODO_*.md(N) | wc -l | xargs printf "TODO: %s\n" && ls .spx/sessions/DOING_*.md(N) | wc -l | xargs printf "DOING: %s\n"": This command uses shell operators that require approval for safety

# Avoid parameter substitution
Error: Bash command permission check failed for pattern "!for f (.spx/sessions/DOING_*) print mv $f ${f/DOING/TODO}": Command contains ${} parameter substitution

# Avoid loops
Error: Bash command permission check failed for pattern "!find .spx/sessions -maxdepth 1 -name 'DOING_*' | while read f; do echo mv "$f" "$(echo "$f" | sed 's/DOING/TODO/')"; done": This Bash command contains multiple operations. The following part requires approval: while read f ;
     do echo mv "$f" "$(echo "$f" | sed ''s/DOING/TODO/'')" ; done

Error: Bash command permission check failed for pattern "!find .spx/sessions -maxdepth 1 -name 'DOING_*' | awk '{new=$0; sub(/DOING/,"TODO",new); print "mv "$0" "new}'": This Bash command contains multiple operations. The following part requires approval: awk '{new=$0;
     sub(/DOING/,""TODO"",new); print ""mv ""$0"" ""new}'
```

---

## For Claude Agents Modifying This Marketplace

### ⛔ Subagent Restrictions

**NEVER use subagents (Agent tool) to create or modify any file.** All file creation and modification must happen in the main conversation context using Read, Edit, and Write tools directly. Subagents are for research, exploration, and auditing only.

### ⛔ Path Restrictions

**NEVER write to these locations:**

- `.claude/` - Requires user permission for every operation, breaks workflow
- `~/.claude/` - User home directory, not project-specific
- Any path containing `.claude` in user home

**ALWAYS write to project directories:**

- `plugins/` - Plugin code, skills, commands, templates
- `spx/` - Specs as durable map (see [spx/CLAUDE.md](spx/CLAUDE.md))
- `.spx/` - Tool operational files (sessions, cache) - gitignored
- Project root - Package files, config files

**Rationale:** Claude Code requires user permission for every file operation in `.claude/` directories. This creates friction and breaks the development flow. All project artifacts belong in the project directory structure.

### Before Making Changes

1. **Read the context**: Check [CLAUDE.md](CLAUDE.md:1) (this file) for current structure and versioning rules
2. **Check existing commands**: Use Glob to find existing `.md` files in `plugins/*/commands/`
3. **Review plugin structure**: Each plugin has its own `plugin.json` in `.claude-plugin/`

### After Adding/Modifying Commands or Skills

**⚠️ CRITICAL: Version bumps must be in the SAME commit as your changes.** See [Version Bump Workflow](#version-bump-workflow) above.

**Workflow:**

1. **Make your changes** to skills, commands, templates, etc.

2. **Determine version bump type** (see [Version Management](#version-management) above):
   - **MAJOR** (0.x.x → 1.x.x): ⛔ NEVER unless user explicitly requests
   - **MINOR** (0.3.x → 0.4.x): New command/skill OR major functional change
   - **PATCH** (0.3.x → 0.3.1): Bug fixes, refactoring, small changes (MOST COMMON)

3. **Update plugin.json version** in the same working session:

   ```bash
   # Location: plugins/{plugin-name}/.claude-plugin/plugin.json
   # Update "version" field according to rules above
   ```

4. **Update marketplace description** (only if needed):

   ```bash
   # Location: .claude-plugin/marketplace.json
   # Update description for the modified plugin (only if description changes)
   ```

5. **Document changes**: Update this [CLAUDE.md](CLAUDE.md:1) file if adding new commands/skills to the plugin tables

6. **Stage and commit EVERYTHING together** in ONE commit:

   ```bash
   git add plugins/{plugin-name}/ plugins/{plugin-name}/.claude-plugin/plugin.json
   git commit -m "type(scope): your changes including version bump"
   ```

**Validation**: The pre-commit hook automatically validates marketplace and plugins. If validation fails, the commit is blocked until errors are fixed.

### Quick Reference: File Locations

```
outcomeeng/claude/                  # Marketplace: outcomeeng
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog
├── .spx/                          # Tool operational (gitignored)
│   └── sessions/                  # Session handoffs
├── plugins/
│   ├── claude/                   # Version: 0.1.2 — Meta-skills
│   │   └── skills/
│   │       ├── creating-skills/
│   │       ├── creating-commands/
│   │       ├── creating-subagents/
│   │       ├── auditing-skills/
│   │       ├── auditing-commands/
│   │       └── auditing-subagents/
│   ├── code/                     # Version: 0.0.3
│   │   └── skills/
│   │       └── coding-autonomously/
│   ├── core/                     # Version: 0.4.31
│   │   ├── commands/
│   │   │   ├── commit.md
│   │   │   ├── handoff.md
│   │   │   └── pickup.md
│   │   └── skills/
│   │       └── committing-changes/
│   ├── frontend/                 # Version: 0.0.2
│   │   └── skills/
│   │       └── designing-frontend/
│   ├── prose/                    # Version: 0.1.3
│   │   └── skills/
│   │       ├── writing-prose/
│   │       └── reviewing-prose/
│   ├── python/                   # Version: 0.11.4
│   │   ├── commands/
│   │   │   └── auto-python.md
│   │   └── skills/
│   │       └── (6 skills)
│   ├── spec-tree/                # Version: 0.4.1 — Spec Tree (current)
│   │   └── skills/
│   │       └── (7 skills)
│   ├── specs/                    # Version: 0.5.7 (legacy)
│   │   └── skills/
│   │       ├── managing-specs/
│   │       └── understanding-specs/
│   ├── spx/                      # Version: 0.10.0 — SPX commands
│   │   ├── commands/
│   │   │   ├── clarify.md
│   │   │   ├── commit.md
│   │   │   ├── handoff.md
│   │   │   ├── pickup.md
│   │   │   └── rtfm.md
│   │   └── skills/
│   │       └── committing-changes/
│   ├── spx-legacy/               # Version: 0.1.3 (deprecated → spec-tree)
│   │   └── skills/
│   │       └── (9 skills)
│   ├── test/                     # Version: 0.4.0
│   │   └── skills/
│   │       ├── testing/
│   │       └── reviewing-tests/
│   └── typescript/               # Version: 0.9.0
│       ├── commands/
│       │   └── auto-typescript.md
│       └── skills/
│           └── (7 skills)
├── spx/                           # Specs as durable map
│   └── CLAUDE.md                 # Specs directory guide
└── CLAUDE.md                      # This file
```

### Versioning Reminder

**When in doubt:**

- Most changes = PATCH version bump
- New items or major changes = MINOR version bump
- Major version stays at 0.x.x unless user requests otherwise

## How to commit

Always invoke the skill `/committing-changes` and adhere to its git commit message guidance.

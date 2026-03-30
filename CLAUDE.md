# Outcome Engineering Plugin Marketplace

Claude Code plugin marketplace (`outcomeeng/claude`) for spec-driven development with [Outcome Engineering](https://outcome.engineering).

## Marketplace Is a Product

We develop this marketplace as a product using its own Spec Tree. The product specs are in `spx/` (the durable map).

## Historical Context

The Outcome Engineering methodology has evolved through three generations. Only the current one is active.

| Generation              | Plugin       | Directory     | Node types                     | Context skill          | Status      |
| ----------------------- | ------------ | ------------- | ------------------------------ | ---------------------- | ----------- |
| 1st (Jul 2025–Jan 2026) | `specs`      | `specs/work/` | `capability → feature → story` | `/understanding-specs` | **Legacy**  |
| 2nd (Jan–Mar 2026)      | `spx-legacy` | `spx/`        | `capability → feature → story` | `/understanding-spx`   | **Legacy**  |
| 3rd (Mar 2026–)         | `spec-tree`  | `spx/`        | `enabler`, `outcome`           | `/contextualizing`     | **Current** |

**What changed across generations:**

- **1st → 2nd**: Moved from `specs/work/` to `spx/`, adopted durable map principles and sparse integer ordering. The three-level hierarchy (`capability/feature/story`) remained.
- **2nd → 3rd**: Replaced the fixed three-level hierarchy with two recursive node types (`enabler`, `outcome`) that nest to arbitrary depth. Replaced `understanding-spx` with `contextualizing`. Merged the separate `spx` and `code` plugins into `spec-tree`.

**Why legacy plugins still exist:** The `specs` and `spx-legacy` plugins remain in the repository for projects that haven't migrated. They are not installed in new projects.

## Critical Rules

- ⚠️ **NEVER answer ANY question without invoking at least one skill first** - If the question touches testing, specs, code, architecture, or any topic covered by a skill, invoke the relevant skill BEFORE answering. Skills are the authoritative source — not grep results, not existing files, not your training data. See skill table below.
- ⚠️ **NEVER write code without invoking a skill first** - See skill table below
- ⚠️ **NEVER write tests in `tests/`** - Write in `spx/.../tests/` (co-located with specs)
- ⚠️ **NEVER manually navigate `spx/` hierarchy** - Use `/contextualizing spx/path/to/node` skill
- ⚠️ **ALWAYS read CLAUDE.md in subdirectories** - When working with files in `spx/`, or any other directory, read that directory's CLAUDE.md FIRST if it exists
- ⚠️ **Skills are ALWAYS authoritative over existing files** - When a skill template prescribes a structure (e.g., Architectural Constraints table), follow the skill — not patterns found in existing spec files. Existing files may contain non-standard sections added before skills existed. Never infer framework conventions from existing files; always read the skill.
- ⚠️ **NEVER maintain backward compatibility** - When rewriting a module, replace it entirely. No legacy aliases, no re-exports of old names, no shims. Update all imports across the codebase to use the new API.
- ⚠️ **NEVER reference specs or decisions from code** - No `ADR-21`, `PDR-13`, or similar in Python comments or docstrings. Specs are the source of truth; code should not duplicate or point to them. The `semgrep` rule enforces this.
- ⚠️ **NEVER edit `package.json` for dependency changes** - Use `just add`/`just remove` — they update package.json, lockfile, and venv atomically
- ⚠️ **NEVER manually delete untracked files or empty directories** - Git doesn't track empty dirs; `.DS_Store` and `__pycache__` are gitignored artifacts. Use `just run clean` to remove them
- ⚠️ **NEVER use agents to create or modify ANY files** - Agents (subagents, background agents) must ONLY be used for read-only research: searching code, reading files, running read-only commands. ALL file creation, editing, and writing MUST happen in the main conversation context. Agents lack context, create unauthorized files, conflict on shared config, and make unasked-for changes.
- ✅ **Always use `just run test`** - Never bare pytest (just run loads .env automatically)
- ✅ **When uncertain, ASK STRUCTURED QUESTIONS. Never guess implementation patterns, test methodology or requirements.**
- ✅ **Use `AskUserQuestion` for structured questions with predefined options.** Do NOT use it for open-ended questions where the user needs to provide free-form context — just ask in plain text instead.
- ✅ **When you are wrong, KEEP ASKING STRUCTURED QUESTIONS. Never assume that you are bothering the user. You are doing the right thing.**

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
just check
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

1. **Foundational skill** (e.g., `/testing`) - Contains core principles, methodology, and language-agnostic patterns
2. **Language-specific skills** (e.g., `/testing-python`, `/testing-typescript`) - Reference the foundational skill, provide only language-specific implementations

For spec-tree users, `/testing` from the spec-tree plugin is a superset that also covers tree-specific concerns. The language-specific skills use unqualified names (`/testing`) so they resolve to whichever foundational skill is installed.

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

## Legacy Plugin

Standalone commit workflow and foundational testing for projects without the spx CLI. Spec-tree users should use `spec-tree:testing` and `spec-tree:auditing-tests` instead, which are supersets.

### Skills

| Skill                 | Purpose                                                       |
| --------------------- | ------------------------------------------------------------- |
| `/committing-changes` | Comprehensive git commit message guidance                     |
| `/testing`            | Foundational testing methodology (5 stages, 5 factors)        |
| `/reviewing-tests`    | Foundational test review protocol (loaded by language skills) |

### Commands

| Command    | Purpose                                             |
| ---------- | --------------------------------------------------- |
| `/commit`  | Git commit with Conventional Commits (auto-context) |
| `/handoff` | Create timestamped context handoff                  |
| `/pickup`  | Load and continue from previous handoff             |

## HDL Plugin

HDL engineering skills for VHDL and SystemVerilog code review.

### Skills

| Skill                      | Purpose                                                              |
| -------------------------- | -------------------------------------------------------------------- |
| `/reviewing-vhdl`          | Idiomatic VHDL-2008 review with synthesizability analysis            |
| `/reviewing-systemverilog` | Idiomatic SystemVerilog IEEE 1800-2017 review for Vivado and Quartus |

## Frontend Plugin

Frontend design and coding skills and commands.

### Skills

| Skill                | Purpose                                                  |
| -------------------- | -------------------------------------------------------- |
| `designing-frontend` | Create distinctive, production-grade frontend interfaces |

## Prose Plugin

Prose craft skills for writing and reviewing.

### Skills

| Skill                  | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| `/standardizing-prose` | Prose anti-patterns enforced across all skills (reference) |
| `/writing-prose`       | Write varied, specific, human prose (always active)        |
| `/reviewing-prose`     | Review and edit prose for formulaic patterns (on request)  |

## TypeScript Plugin

Complete TypeScript development workflow with testing, implementation, and review.

### Skills

| Skill                               | Purpose                                           |
| ----------------------------------- | ------------------------------------------------- |
| `/testing-typescript`               | TypeScript-specific testing patterns              |
| `/coding-typescript`                | Implementation workhorse with remediation loop    |
| `/auditing-typescript`              | Strict code audit with zero-tolerance             |
| `/auditing-typescript-tests`        | TypeScript test evidence audit (4-property model) |
| `/architecting-typescript`          | ADR producer with testing strategy                |
| `/auditing-typescript-architecture` | ADR audit against testing principles              |

### Core Principles

- No mocking - dependency injection only
- Reality is the oracle
- Behavior testing, not implementation testing
- Tests at appropriate levels (Level 1/Level 2/Level 3)

## Python Plugin

Complete Python development workflow with testing, implementation, and review.

### Skills

| Skill                           | Purpose                                        |
| ------------------------------- | ---------------------------------------------- |
| `/testing-python`               | Python-specific testing patterns               |
| `/coding-python`                | Implementation workhorse with remediation loop |
| `/auditing-python`              | Strict code audit with zero-tolerance          |
| `/auditing-python-tests`        | Python test evidence audit (4-property model)  |
| `/architecting-python`          | ADR producer with testing strategy             |
| `/auditing-python-architecture` | ADR audit against testing principles           |

### Core Principles

- No mocking - dependency injection only
- Reality is the oracle
- Behavior testing, not implementation testing
- Tests at appropriate levels (Level 1/Level 2/Level 3)

## Spec Tree Plugin

Spec-driven development with the Spec Tree framework. Three phases: spec-tree maintenance, implementation, commit.

### Skills

| Skill                         | Phase | Purpose                                                                     |
| ----------------------------- | ----- | --------------------------------------------------------------------------- |
| `/understanding`              | 1     | Foundation skill — loaded before any other                                  |
| `/contextualizing`            | 1     | Show status, progress, what exists                                          |
| `/bootstrapping`              | 1     | Interview user, scaffold new spec tree                                      |
| `/authoring`                  | 1     | Add, define, create specs, decisions, and nodes                             |
| `/decomposing`                | 1     | Break down, split, scope work                                               |
| `/refactoring`                | 1     | Move nodes, re-scope, extract shared enablers                               |
| `/aligning`                   | 1     | Review, check consistency, audit, find gaps                                 |
| `/testing`                    | 2     | Write tests driven by spec assertions (superset of legacy plugin)           |
| `/auditing-tests`             | 2     | Audit test evidence quality: coupling, falsifiability, alignment, coverage  |
| `/auditing-product-decisions` | 2     | Audit PDR evidence: content, invariants, compliance, voice, downstream flow |
| `/coding`                     | 2     | TDD flow: architect, test, code + review gates                              |
| `/committing-changes`         | 3     | Conventional Commits with selective staging                                 |

### Commands

| Command      | Purpose                                                       |
| ------------ | ------------------------------------------------------------- |
| `/bootstrap` | Set up a new spec tree (invokes `/bootstrapping`)             |
| `/author`    | Author a spec tree artifact (auto-detects type)               |
| `/commit`    | Git commit with Conventional Commits (auto-context)           |
| `/realize`   | Run TDD flow on a subtree or discover work from `spx/EXCLUDE` |
| `/rtfm`      | Stop ad hoc work and follow the methodology                   |
| `/clarify`   | Clarify ambiguous requirements                                |
| `/handoff`   | Create timestamped context handoff                            |
| `/pickup`    | Load and continue from previous handoff                       |

## Discovering Other Installed Skills

Search for `SKILL.md` in `.claude/plugins/cache/{marketplace-name}/{plugin-name}/`

## Proactive Skill Invocation

Certain skills must be invoked **automatically** when specific conditions are met, without waiting for explicit user request.

**BEFORE implementing any work item**, you MUST:

1. **Invoke `/contextualizing`** on the target node
   - **Trigger**: User requests implementation of a work item
   - **Purpose**: Load complete context hierarchy (product → decisions → ancestors → target)
   - **Example**: User says "implement this outcome" → STOP and invoke `/contextualizing` FIRST
   - **Non-negotiable**: Do NOT read spec files directly without invoking this skill

2. **Invoke `/authoring`** when creating specs or nodes
   - **Trigger**: User requests creating a product spec, ADR, PDR, enabler, or outcome
   - **Purpose**: Access templates, understand index assignment
   - **Example**: User says "create an outcome for search" → STOP and invoke `/authoring`
   - **Critical**: Templates are in the `understanding` skill's directory, NOT in the project

**Pattern**: These skills are preparatory and blocking. You MUST invoke them BEFORE writing code or documents.

**Rationale**: Without these skills, you will:

- Miss requirements and violate ADRs
- Search for templates that don't exist in the project
- Create nodes with incorrect indices
- Generate specs with wrong structure

## Naming Skills

The `name` field in SKILL.md YAML frontmatter is how users invoke your skill (`/skill-name`).

**Match user speech patterns:**

- Use domain acronyms: `authoring` not `authoring-spec-tree-artifacts`
- Use terms users actually say: `testing-python` not `python-unit-test-framework`
- Think "CD-ROM" not "Compact Disc Read Only Memory"

**Directory name must match:**

- Directory: `skills/authoring/`
- YAML name: `name: authoring`
- User invokes: `/authoring`

**Examples from this marketplace:**

```yaml
# ✅ Good: matches user speech
name: authoring
# Users say "author a spec"

name: testing-typescript
# Users say "test TypeScript code"

name: bootstrapping
# Users say "bootstrap the spec tree"
```

```yaml
# ❌ Bad: nobody says these
name: authoring-spec-tree-artifacts
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

**Spec Tree skills (differentiating similar skills):**

```yaml
# ✅ Good: directive with negative constraint
name: contextualizing
description: >-
  ALWAYS invoke this skill when asking about status, progress, or what exists in the spec tree.
  NEVER work on any part of the spec tree without loading context through this skill first.

name: authoring
description: >-
  ALWAYS invoke this skill when adding, defining, or creating specs, decisions, or nodes.
  NEVER author spec tree artifacts without this skill.

name: decomposing
description: >-
  ALWAYS invoke this skill when breaking down, splitting, scoping, or structuring spec tree nodes.
  NEVER decompose specs without this skill.
```

**Why these work:**

- `ALWAYS` tells Claude when to activate (specific triggers)
- `NEVER` tells Claude what NOT to do without the skill (negative constraint)
- Natural language users actually say ("author a spec" not "spec authoring protocol")
- Short and direct

```yaml
# ❌ Bad: passive style (77% activation)
name: contextualizing
description: Load spec tree context before working. Use when starting implementation.
# Problem: Claude will just read the files directly instead of invoking the skill

# ❌ Bad: formal jargon
name: authoring
description: Systematic spec creation with outcome hypotheses and typed assertions.
# Problem: Nobody says "outcome hypotheses"
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

**Quoting:** When a fallback echo string contains double quotes (e.g., a command name), use single quotes for the outer string:

```bash
# ✅ Single quotes outside, double quotes inside
!`spx session list || echo 'Ask user to install: "npm install --global @outcomeeng/spx"'`

# ❌ Double quotes with escapes — triggers "ambiguous syntax" permission error
!`spx session list || echo "Ask user to install: \"npm install --global @outcomeeng/spx\""`
```

**Other restrictions:**

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

### ⛔ File Removal Restrictions

**Tracked files with no changes:** Use `git rm` to remove files that are committed in git and have no uncommitted modifications.

**All other files:** You CANNOT remove files that are untracked or have uncommitted changes. Do not attempt to circumvent this restriction. Instead, **ALWAYS** provide the exact `rm` command to the user and **WAIT** until the user has confirmed they have executed it before proceeding.

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

6. **Update bootstrapping template**: If the change affects skill structure, commands, or conventions that new projects inherit, update `plugins/spec-tree/skills/bootstrapping/templates/spx-claude.md` to match

7. **Stage and commit EVERYTHING together** in ONE commit:

   ```bash
   git add plugins/{plugin-name}/ plugins/{plugin-name}/.claude-plugin/plugin.json
   git commit -m "type(scope): your changes including version bump"
   ```

**Validation**: Run `just check` before committing. The pre-commit hook also validates, but catching errors earlier is faster.

### Quick Reference: File Locations

```
outcomeeng/claude/                  # Marketplace: outcomeeng
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog
├── .spx/                          # Tool operational (gitignored)
│   └── sessions/                  # Session handoffs
├── plugins/
│   ├── claude/                   # Meta-skills for plugin development
│   │   └── skills/
│   │       ├── creating-skills/
│   │       ├── creating-commands/
│   │       ├── creating-subagents/
│   │       ├── auditing-skills/
│   │       ├── auditing-commands/
│   │       └── auditing-subagents/
│   ├── legacy/                   # Standalone commit + testing (no spx CLI)
│   │   ├── commands/
│   │   │   ├── commit.md
│   │   │   ├── handoff.md
│   │   │   └── pickup.md
│   │   └── skills/
│   │       ├── committing-changes/
│   │       ├── testing/
│   │       └── auditing-tests/
│   ├── frontend/
│   │   └── skills/
│   │       └── designing-frontend/
│   ├── hdl/                       # HDL engineering
│   │   └── skills/
│   │       ├── reviewing-vhdl/
│   │       └── reviewing-systemverilog/
│   ├── prose/
│   │   └── skills/
│   │       ├── standardizing-prose/
│   │       ├── writing-prose/
│   │       └── reviewing-prose/
│   ├── python/
│   │   └── skills/
│   │       └── (6 skills)
│   ├── spec-tree/                # Spec Tree — 3 phases
│   │   ├── commands/
│   │   │   ├── author.md
│   │   │   ├── bootstrap.md
│   │   │   ├── clarify.md
│   │   │   ├── commit.md
│   │   │   ├── handoff.md
│   │   │   ├── pickup.md
│   │   │   ├── realize.md
│   │   │   └── rtfm.md
│   │   └── skills/
│   │       └── (11 skills)
│   └── typescript/
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

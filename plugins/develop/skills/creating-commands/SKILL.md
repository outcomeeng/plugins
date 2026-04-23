---
name: creating-commands
description: >-
  ALWAYS invoke this skill when creating or editing slash commands.
  NEVER create slash commands without this skill.
---

<objective>
Create effective slash commands for Claude Code that enable users to trigger reusable prompts with `/command-name` syntax. Slash commands expand as prompts in the current conversation, allowing teams to standardize workflows and operations. This skill teaches you to structure commands with XML tags, YAML frontmatter, dynamic context loading, and intelligent argument handling.

Read `/standardizing-agent-prompts` for voice, description, constraint, and anti-pattern conventions before writing prompt text.
</objective>

<quick_start>

<workflow>
1. Create `.claude/commands/` directory (project) or use `~/.claude/commands/` (personal)
2. Create `command-name.md` file
3. Add YAML frontmatter (at minimum: `description`)
4. Write command prompt
5. Test with `/command-name [args]`

</workflow>

<example>
**File**: `.claude/commands/optimize.md`

```markdown
---
description: Analyze this code for performance issues and suggest optimizations
---

Analyze the performance of this code and suggest three specific optimizations:
```

**Usage**: `/optimize`

Claude receives the expanded prompt and analyzes the code in context.
</example>
</quick_start>

<xml_structure>
All generated slash commands should use XML tags in the body (after YAML frontmatter) for clarity and consistency.

<required_tags>

**`<objective>`** - What the command does and why it matters

```markdown
<objective>
What needs to happen and why this matters.
Context about who uses this and what it accomplishes.
</objective>
```

**`<process>` or `<steps>`** - How to execute the command

```markdown
<process>
Sequential steps to accomplish the objective:
1. First step
2. Second step
3. Final step
</process>
```

**`<success_criteria>`** - How to know the command succeeded

```markdown
<success_criteria>
Clear, measurable criteria for successful completion.
</success_criteria>
```

</required_tags>

<conditional_tags>

**`<context>`** - When loading dynamic state or files

```markdown
<context>
Current state: ! `git status`
Relevant files: @ package.json
</context>
```

(Note: Remove the space after @ in actual usage)

**`<verification>`** - When producing artifacts that need checking

```markdown
<verification>
Before completing, verify:
- Specific test or check to perform
- How to confirm it works
</verification>
```

**`<testing>`** - When running tests is part of the workflow

```markdown
<testing>
Run tests: ! `npm test`
Check linting: ! `npm run lint`
</testing>
```

**`<output>`** - When creating/modifying specific files

```markdown
<output>
Files created/modified:
- `./path/to/file.ext` - Description
</output>
```

</conditional_tags>

<structure_example>

```markdown
---
name: example-command
description: Does something useful
argument-hint: [input]
---

<objective>
Process $ARGUMENTS to accomplish [goal].

This helps [who] achieve [outcome].
</objective>

<context>
Current state: ! `relevant command`
Files: @ relevant/files
</context>

<process>
1. Parse $ARGUMENTS
2. Execute operation
3. Verify results
</process>

<success_criteria>

- Operation completed without errors
- Output matches expected format

</success_criteria>
```

</structure_example>
</xml_structure>

<intelligence_rules>

**Simple commands** (single operation, no artifacts):

- Required: `<objective>`, `<process>`, `<success_criteria>`
- Example: `/check-todos`, `/first-principles`

**Complex commands** (multi-step, produces artifacts):

- Required: `<objective>`, `<process>`, `<success_criteria>`
- Add: `<context>` (if loading state), `<verification>` (if creating files), `<output>` (what gets created)
- Example: `/commit`, `/create-prompt`, `/run-prompt`

**Commands with dynamic arguments**:

- Use `$ARGUMENTS` in `<objective>` or `<process>` tags
- Include `argument-hint` in frontmatter
- Make it clear what the arguments are for

**Commands that produce files**:

- Always include `<output>` tag specifying what gets created
- Always include `<verification>` tag with checks to perform

**Commands that run tests/builds**:

- Include `<testing>` tag with specific commands
- Include pass/fail criteria in `<success_criteria>`

</intelligence_rules>

<arguments_intelligence>
Determine whether a command needs arguments:

**Needs arguments** — task operates on user-specified data:

- Use `$ARGUMENTS` for single input: `Fix issue #$ARGUMENTS`
- Use `$1`, `$2`, `$3` for structured input: `Review PR #$1 with priority $2`
- Add `argument-hint` in frontmatter

**No arguments** — task operates on implicit context (conversation, known files, project state):

- Omit `argument-hint` and don't reference `$ARGUMENTS`

For detailed examples and patterns, see [${CLAUDE_SKILL_DIR}/references/arguments.md](references/arguments.md).

</arguments_intelligence>

<file_structure>

**Project commands**: `.claude/commands/`

- Shared with team via version control
- Shows `(project)` in `/help` list

**Personal commands**: `~/.claude/commands/`

- Available across all your projects
- Shows `(user)` in `/help` list

**File naming**: `command-name.md` → invoked as `/command-name`
</file_structure>

<yaml_frontmatter>

<field name="description">
**Required** - Describes what the command does

```yaml
description: Analyze this code for performance issues and suggest optimizations
```

Shown in the `/help` command list.
</field>

<field name="argument-hint">
**Optional** - Tells users what arguments the command expects

```yaml
argument-hint: [issue-number]
argument-hint: <pr-number> <priority> <assignee>
```

Shown in autocomplete. Omit for self-contained commands that don't take arguments.
</field>

<field name="allowed-tools">
**Optional** - Restricts which tools Claude can use

```yaml
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
```

**Formats**:

- Array: `allowed-tools: [Read, Edit, Write]`
- Single tool: `allowed-tools: SequentialThinking`
- Bash restrictions: `allowed-tools: Bash(git add:*)`

If omitted: All tools available
</field>
</yaml_frontmatter>

<dynamic_context>

Execute bash commands before the prompt using the exclamation mark prefix directly before backticks (no space between).

**Note:** Examples below show a space after the exclamation mark to prevent execution during skill loading. In actual slash commands, remove the space.

Example:

```markdown
---
description: Create a git commit
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
---

<context>
- Current git status: ! `git status`
- Current git diff: ! `git diff HEAD`
- Current branch: ! `git branch --show-current`
- Recent commits: ! `git log --oneline -10`
</context>

<process>
Based on the above changes, create a single git commit.
</process>
```

The bash commands execute and their output is included in the expanded prompt.
</dynamic_context>

<file_references>

Use `@` prefix to reference specific files:

```markdown
---
description: Review implementation
---

Review the implementation in @ src/utils/helpers.js
```

(Note: Remove the space after @ in actual usage)

Claude can access the referenced file's contents.
</file_references>

<best_practices>

**1. Always use XML structure**

```yaml
# All slash commands should have XML-structured bodies
```

After frontmatter, use XML tags:

- `<objective>` - What and why (always)
- `<process>` - How to do it (always)
- `<success_criteria>` - Definition of done (always)
- Additional tags as needed (see xml_structure section)

**2. Clear descriptions**

```yaml
# Good
description: Analyze this code for performance issues and suggest optimizations

# Bad
description: Optimize stuff
```

**3. Use dynamic context for state-dependent tasks**

```markdown
Current git status: ! `git status`
Files changed: ! `git diff --name-only`
```

**4. Restrict tools when appropriate**

```yaml
# For git commands - prevent running arbitrary bash
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)

# For analysis - thinking only
allowed-tools: SequentialThinking
```

**5. Use $ARGUMENTS for flexibility**

```markdown
Find and fix issue #$ARGUMENTS
```

**6. Reference relevant files**

```markdown
Review @ package.json for dependencies
Analyze @ src/database/* for schema
```

(Note: Remove the space after @ in actual usage)
</best_practices>

<common_patterns>

Common command patterns with full examples are in [${CLAUDE_SKILL_DIR}/references/patterns.md](references/patterns.md):

- **Simple analysis** — single operation, no state (e.g., security review)
- **Git workflow** — state-dependent with `<context>` and `allowed-tools`
- **Parameterized** — uses `$ARGUMENTS` with `argument-hint`
- **File-specific** — combines `@ $ARGUMENTS` file references with analysis

</common_patterns>

<reference_guides>

**Arguments reference**: [${CLAUDE_SKILL_DIR}/references/arguments.md](references/arguments.md)

- $ARGUMENTS variable
- Positional arguments ($1, $2, $3)
- Parsing strategies
- Examples from official docs

**Patterns reference**: [${CLAUDE_SKILL_DIR}/references/patterns.md](references/patterns.md)

- Git workflows
- Code analysis
- File operations
- Security reviews
- Examples from official docs

**Tool restrictions**: [${CLAUDE_SKILL_DIR}/references/tool-restrictions.md](references/tool-restrictions.md)

- Bash command patterns
- Security best practices
- When to restrict tools
- Examples from official docs

</reference_guides>

<generation_protocol>

1. **Analyze**: Determine purpose, whether arguments are needed, complexity level (simple vs. complex), and security profile
2. **Frontmatter**: Add `description` (required), `argument-hint` (if arguments needed), `allowed-tools` (if tool restrictions needed)
3. **Body**: Use XML tags — always `<objective>`, `<process>`, `<success_criteria>`; add `<context>`, `<verification>`, `<testing>`, `<output>` as needed (see `<intelligence_rules>`)
4. **Arguments**: Use `$ARGUMENTS` or positional `$1`/`$2` in tags (see `<arguments_intelligence>`)
5. **Save**: Project commands in `.claude/commands/`, personal in `~/.claude/commands/`

</generation_protocol>

<success_criteria>
A well-structured slash command meets these criteria:

**YAML Frontmatter**:

- `description` field is clear and concise
- `argument-hint` present if command accepts arguments
- `allowed-tools` specified if tool restrictions needed

**XML Structure**:

- All three required tags present: `<objective>`, `<process>`, `<success_criteria>`
- Conditional tags used appropriately based on complexity
- No raw markdown headings in body
- All XML tags properly closed

**Arguments Handling**:

- `$ARGUMENTS` used when command operates on user-specified data
- Positional arguments (`$1`, `$2`, etc.) used when structured input needed
- No `$ARGUMENTS` reference for self-contained commands

**Functionality**:

- Command expands correctly when invoked
- Dynamic context loads properly (bash commands, file references)
- Tool restrictions prevent unauthorized operations
- Command accomplishes intended purpose reliably

**Quality**:

- Clear, actionable instructions in `<process>` tag
- Measurable completion criteria in `<success_criteria>`
- Appropriate level of detail (not over-engineered for simple tasks)
- Examples provided when beneficial

</success_criteria>

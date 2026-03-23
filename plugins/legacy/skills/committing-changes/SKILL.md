---
name: committing-changes
description: >-
  ALWAYS invoke this skill when committing changes or when user says "commit".
  NEVER run git commit without this skill.
---

<objective>
Write effective git commit messages following Conventional Commits standard with selective staging, atomic commits, and domain-specific type conventions.
</objective>

<quick_start>

1. **Run project validation first**: Check CLAUDE.md for `just check`, `pnpm run check`, etc.
2. Review changes: `git status`, `git diff`
3. **Classify changes by concern** — group by type+scope, split if multiple groups
4. Stage specific files for ONE concern: `git add path/to/file.ts` (never `git add .`)
5. Write message: `type(scope): description` (imperative, under 50 chars)
6. Commit, then repeat from step 4 for remaining concerns

</quick_start>

<success_criteria>

A successful commit has:

- Concerns classified before staging (type+scope grouping applied)
- One concern per commit (split when types or scopes differ)
- Selective staging (specific files, not `git add .`)
- Conventional Commits format (type, optional scope, imperative description)
- No debug code or unintended files
- Clean diff review confirms expected changes only

</success_criteria>

<capabilities>

- Guides selective file staging (never `git add .`)
- Writes commit messages in Conventional Commits format
- Verifies atomic commit principles
- Adapts commit types to project domain

</capabilities>

<exclusions>

This skill does NOT:

- Push commits to remote
- Create pull requests
- Modify git configuration
- Bypass pre-commit hooks

</exclusions>

<context_gathering>

**Before creating any commit, gather context:**

| Source           | Gather                                                  |
| ---------------- | ------------------------------------------------------- |
| **git status**   | Staged, unstaged, untracked files                       |
| **git diff**     | Actual changes to commit                                |
| **git log**      | Recent commit style for consistency                     |
| **Project docs** | Custom commit types (CLAUDE.md, CONTRIBUTING.md)        |
| **Conversation** | User's intent - what story/issue does this commit solve |

</context_gathering>

<review_workflow_context>

**When invoked from a reviewing skill** (e.g., `reviewing-python`, `reviewing-typescript`):

This skill may be referenced during the commit phase of a code review. In that context:

1. **Committing is the seal of approval** — Only commit after verdict is APPROVED
2. **Scope to work item** — Stage only files from the approved work item:
   - Implementation files
   - Co-located tests (in `spx/.../tests/`)
3. **Include work item reference** — Add `Refs: {capability}/{feature}/{story}` in footer
4. **Verify tests pass** — All tests must pass before committing

The reviewing skill provides the specific file list and work item context. This skill provides the commit protocol mechanics.

</review_workflow_context>

<concern_separation>

**MANDATORY: Analyze before staging. Never stage everything then ask about splitting.**

After gathering context (`git status`, `git diff`), classify every changed and untracked file by concern before touching `git add`. A concern is one logical purpose that gets one commit type and one scope.

**Classification procedure:**

1. List every changed/untracked file.
2. Assign each file a commit type (`spec`, `feat`, `fix`, `refactor`, `docs`, etc.).
3. Assign each file a scope (module, plugin, component).
4. Group files that share the same type AND scope — each group is one commit.

**Split signals — if ANY of these are true, you MUST split into multiple commits:**

- Files need different commit types (e.g., `spec` for a design doc + `feat` for implementation)
- Files belong to different scopes (e.g., `methodology/` spec + `plugins/` code)
- Changes serve different purposes even within the same directory
- A design/spec document and its implementation are both present

**Commit ordering:**

When splitting, commit in dependency order:

1. Specs and design documents first (they define what follows)
2. Infrastructure and enablers second
3. Implementation last
4. Tests alongside whatever they test

**Example:**

```text
Changed files:
  methodology/skills/skill-structure.md   → spec(spec-tree)
  plugins/spec-tree/**                     → feat(spec-tree)

→ Two commits:
  1. spec(spec-tree): define methodology
  2. feat(spec-tree): add plugin implementation
```

**Never ask the user whether to split.** Apply the classification procedure. If the result is multiple groups, commit them separately. Separation of concerns is not a preference — it is a requirement.

</concern_separation>

<verification_protocol>

**Step 0: Run Project-Specific Validation (BEFORE Staging)**

Before staging any files, check CLAUDE.md for project-specific validation commands and run them. This prevents having to re-stage after auto-fixes.

```bash
# Check CLAUDE.md for commands like:
just check        # Justfile task runner
just validate
pnpm run check    # pnpm scripts
pnpm run validate
npm run check     # npm scripts
make check        # Makefile targets
make lint
```

**Why before staging?** Many project commands (formatters, linters with auto-fix) modify files. Running them after staging means you need to re-stage the fixed files. Run validation first, then stage.

**Step 1: Selective Staging**

```bash
# NEVER do this
git add .

# ALWAYS stage specific files
git add path/to/file1.ts path/to/file2.ts
```

**Rules:**

- One logical change per commit
- Review each `??` untracked file consciously
- Exclude experimental/incomplete work
- Use explicit paths, not wildcards

**Step 2: Diff Review**

```bash
git diff --cached           # Review actual changes
git diff --cached --name-only  # Verify file list
```

**Checklist:**

- [ ] File count matches scope of change
- [ ] No surprise files included
- [ ] All changes related to single purpose
- [ ] No debug code (console.log, print statements, temp comments)

**Step 3: Atomic Commit Verification**

- [ ] Single purpose - does exactly one thing
- [ ] Independent - can be reverted without breaking other features
- [ ] Complete - includes everything needed for the change to work

**Red Flags - DO NOT COMMIT IF:**

- More than 10 files for a simple fix
- Changes span unrelated modules
- Experimental code mixed with stable fixes
- New unintended files included

</verification_protocol>

<message_format>

```text
<type>[(scope)]: <description>

[optional body]

[optional footer(s)]
```

**Subject Line (Required)**

- **Type**: Required (see commit_types section)
- **Scope**: Optional, component/module name
- **Description**: Imperative mood, 50 chars max, no period

```text
feat(auth): add OAuth2 token refresh
fix: handle empty response from API
refactor(db): extract query builder module
```

**Body (Optional)**

- Wrap at 72 characters
- Explain WHAT and WHY, not HOW
- Blank line between subject and body

**Footer (Optional)**

- `BREAKING CHANGE: description` - major version bump
- `Refs: #123` or `Closes #456` - issue references
- Work item refs: `Refs: feature-32/story-27`

</message_format>

<commit_types>

**Standard Types**

| Type         | Purpose                               | SemVer |
| ------------ | ------------------------------------- | ------ |
| **spec**     | Specification only                    | PATCH  |
| **test**     | Add/modify tests                      | PATCH  |
| **feat**     | Implementation of new functionality   | MINOR  |
| **refactor** | Code restructure (no behavior change) | PATCH  |
| **fix**      | Bug fix                               | PATCH  |
| **docs**     | Documentation only                    | PATCH  |
| **style**    | Formatting (no logic change)          | PATCH  |
| **perf**     | Performance improvement               | PATCH  |
| **ci**       | CI/CD changes                         | PATCH  |
| **build**    | Build system, dependencies            | PATCH  |
| **revert**   | Revert previous commit                | varies |

**Domain-Specific Types**

Projects may define custom types:

| Type         | Domain           | Purpose                        |
| ------------ | ---------------- | ------------------------------ |
| **draft**    | Writing projects | New or revised content         |
| **research** | Academic/books   | Research notes                 |
| **meta**     | Process docs     | Process/workflow documentation |

Check project's CLAUDE.md or commit-standards.md for custom types.

**IMPORTANT:** NEVER USE `chore:`. Everything has purpose; use specific type instead

</commit_types>

<breaking_changes>

Mark breaking changes with:

1. **Exclamation suffix**: "feat!: remove deprecated API"
2. **Footer**:

   ```text
   feat: change authentication flow

   BREAKING CHANGE: JWT tokens now expire in 1 hour instead of 24
   ```

</breaking_changes>

<scope_guidelines>

**Use Scope When:**

- Component-specific: `feat(auth): add 2FA support`
- Module changes: `fix(api): handle rate limiting`
- Clear subsystem: `test(db): add connection pool tests`

**Omit Scope When:**

- Single-file change: `fix: correct typo in error message`
- Cross-cutting: `refactor: consolidate error handling`
- Obvious context: `docs: update installation guide`

</scope_guidelines>

<description_guidelines>

**Write for the reader, not the writer.**

Someone scanning `git log --oneline` needs to understand what changed without opening the commit.

**Principle 1: No State Words**

Describe the action, not the prior problem:

```text
# ❌ Describes prior state
fix: handle missing config file
spec(auth): add missing validation rules

# ✅ Describes the action
fix: return defaults when config absent
spec(auth): specify validation rules
```

Avoid: "missing", "broken", "wrong", "bad", "incorrect"

**Principle 2: Content Over Container**

Describe WHAT changed, not WHICH files:

```text
# ❌ Describes the container
spec(session): add stories for timeout feature
docs: update README file

# ✅ Describes the content
spec(session): specify timeout and cleanup behaviors
docs: add installation prerequisites
```

**Principle 3: Don't Repeat the Prefix**

The type already tells you what kind of change:

```text
# ❌ Redundant - prefix already says it's a spec
spec(session): add session management spec
spec(auth): define auth feature stories

# ✅ Just describe the content
spec(session): specify timeout and cleanup behaviors
spec(auth): specify OAuth2 token lifecycle
```

</description_guidelines>

<examples>

**Good Examples**

```text
feat(parser): add support for nested expressions

Enables users to write complex queries with unlimited nesting depth.
Previously limited to 3 levels.

Refs: #234
```

```text
fix: prevent crash on empty config file

Return sensible defaults when config is missing or empty
instead of throwing unhandled exception.
```

```text
refactor: extract validation logic into separate module

Prepares codebase for unit testing by isolating validation
from business logic.
```

**Bad Examples**

```text
# Too vague
fix: bug fixes

# Multiple unrelated changes
feat: add parser and fix tests and update docs

# Contains attribution (NEVER do this)
feat: add export feature (by John)

# Not atomic
refactor: various improvements

# Describes prior state instead of action
fix: handle missing config
spec(auth): add missing validation

# Describes container instead of content
spec(session): add stories for advanced operations
docs: update README file

# Repeats the prefix
spec(session): add session spec
test(auth): add auth tests
```

</examples>

<decision_tree>

```text
Is this a new user feature?           → feat:
Is this fixing a bug?                 → fix:
Is this improving performance?        → perf:
Is this code reorganization?          → refactor:
Is this build/dependencies?           → build:
Is this CI/CD?                        → ci:
Is this documentation?                → docs:
Is this adding/changing tests?        → test:
Is this context/workflow docs?        → ctx: (if project uses it)
```

</decision_tree>

<critical_rules>

1. **NO ATTRIBUTION** - Never include author names in commit messages
2. **IMPERATIVE MOOD** - "add feature" not "added feature" or "adds feature"
3. **NO PERIOD** - Subject line doesn't end with punctuation
4. **SELECTIVE STAGING** - Never use `git add .`
5. **ATOMIC COMMITS** - One logical change per commit

</critical_rules>

<commands_reference>

```bash
# Check what will be committed
git status
git diff --cached
git diff --cached --name-only

# Stage selectively
git add path/to/specific/file.ts

# Commit with multi-line message
git commit -m "$(cat <<'EOF'
feat(scope): subject line here

Body explaining why this change was made.
Wrapped at 72 characters for readability.

Refs: #123
EOF
)"

# View recent commits for style reference
git log --oneline -10
```

</commands_reference>

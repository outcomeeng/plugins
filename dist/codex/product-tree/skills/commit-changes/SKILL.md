---
name: commit-changes
description: >-
  ALWAYS invoke this skill when committing changes or when user says "commit".
  NEVER run git commit without this skill.
allowed-tools: Read, Write, Glob, Grep, Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git rev-parse:*), Bash(git add:*), Bash(git commit:*)
---

<objective>
One atomic local commit per concern. Each commit stages explicit paths, carries a Conventional Commits message, leaves unrelated work in place, and records a verification state.
</objective>

<inputs>

| Input               | Values                                                 | Default when absent |
| ------------------- | ------------------------------------------------------ | ------------------- |
| Verification state  | `passing`, `failing`, or `not-run`                     | `not-run`           |
| Work item reference | A reference string such as a node path or issue number | No `Refs:` footer   |

The verification state describes the latest focused deterministic result for the committed paths; this skill reports it and never runs verification itself.

</inputs>

<success_criteria>

A commit is sound when:

- `git commit` exits zero and the full `HEAD` commit ID differs from its pre-commit value.
- `git diff --cached --name-only` is empty for the committed concern after the commit.
- The result reports the full commit ID, committed paths, remaining paths, and verification state.
- Pre-commit hooks ran normally; a hook rejection returns the exact failure and creates no successful-commit claim.

</success_criteria>

<context>

This skill does NOT:

- Push commits to remote
- Create pull requests
- Modify git configuration
- Bypass pre-commit hooks

</context>

<project_specialization>
After loading this skill, check whether `spx/local/commit-changes.md` exists (path is relative to the repository root). If it does, read it and apply its rules as product-specific additions to the commit workflow (e.g., plugin versioning requirements, additional staging targets, product-specific validation steps).
</project_specialization>

<context_gathering>

**Before creating any commit, gather context:**

| Source           | Gather                                                  |
| ---------------- | ------------------------------------------------------- |
| **git status**   | Staged, unstaged, untracked files                       |
| **git diff**     | Actual changes to commit                                |
| **git log**      | Recent commit style for consistency                     |
| **Product docs** | Custom commit types (AGENTS.md, CONTRIBUTING.md)        |
| **Conversation** | User's intent - what story/issue does this commit solve |

</context_gathering>

<checkpoint_rules>

1. **Commit before another session reads** — When repository writes are authorized, commit the exact current version before another agent session or human is expected or asked to read it, and commit again after any further change before the next such reading. Without that authorization, defer the reading.
2. **New commit after repair** — After repairing a defect in a commit that others have read or reviewed, create a new commit. Do not amend that commit.
3. **Scope to work item** — Stage only files from the work item:
   - Implementation files
   - Co-located tests (in `spx/.../tests/`)
4. **Include work item reference** — When the work item reference input is present, add a `Refs:` footer carrying it verbatim (e.g. `Refs: spx/55-example.domain/21-bar.capability`). When absent, add no footer.
5. **Record verification state** — Report the verification state input. A `failing` or `not-run` state never blocks the commit.

Resolve the specific file list from the invocation inputs and repository state.

</checkpoint_rules>

<concern_separation>

**MANDATORY: Analyze before staging. Never stage everything then ask about splitting.**

After gathering context (`git status`, `git diff`), classify every changed and untracked file by concern before touching `git add`. A concern is one logical purpose that gets one commit type and one scope.

**Classification procedure:**

1. List every changed/untracked file.
2. Assign each file a commit type (`spec`, `feat`, `fix`, `refactor`, `docs`, etc.).
3. Assign each file a scope (module, plugin, component).
4. Group files that share the same type AND scope — each group is one commit.

**Split signals — MUST split into multiple commits if ANY of these are true:**

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
  methodology/skills/skill-structure.md   → spec(product-tree)
  plugins/product-tree/**                     → feat(product-tree)

→ Two commits:
  1. spec(product-tree): define methodology
  2. feat(product-tree): add plugin implementation
```

**Never ask the user whether to split.** Apply the classification procedure. If the result is multiple groups, commit them separately. Separation of concerns is not a preference — it is a requirement.

</concern_separation>

<verification_protocol>

**Step 0: Record Product-Specific Validation State**

Before staging any files, check AGENTS.md for product-specific validation commands. Take the verification state from the input, or `not-run` when absent. This skill is git-only and never runs those commands itself. Continue to the commit in every state; include the product command and the state in the result.

**Step 1: Selective Staging**

ALWAYS stage explicit paths with `git add`; never `git add .` or a wildcard.

**Rules:**

- One logical change per commit
- Review each `??` untracked file consciously
- Keep unrelated experimental work out of the concern; an intentionally incomplete checkpoint is allowed when its staged paths form one coherent concern

**Step 2: Diff Review**

Review `git diff --cached` and verify `git diff --cached --name-only` against the concern's file list.

**Step 3: Atomic Commit Verification**

- [ ] Complete for its stated checkpoint — includes every path needed to preserve that concern, even when verification still fails

**Split or inspect before committing:**

- More than 10 files for a simple fix without a clear generated or cross-cutting reason
- Changes span unrelated modules
- Experimental code mixed with stable fixes
- New unintended files included

These signals require concern reclassification or staging correction. A failing or not-run verification state never appears in this list and never blocks the local commit.

**Step 4: Confirm Commit Postconditions**

Record the full pre-commit and post-commit `HEAD` IDs. After `git commit` exits zero, confirm the IDs differ, inspect `git status --short`, and report the committed paths, remaining paths, and verification state. When a hook or `git commit` fails, preserve its output, confirm no successful commit was created, and return the failure without `--no-verify` or another bypass.

</verification_protocol>

<message_payload>

A commit message is a payload: it spans lines and carries code spans, quotes, or shell metacharacters. It reaches `git commit` through a file, never through a heredoc, a pipe, or an inline `-m` argument.

- ALWAYS: write the message with the file-write tool to a file in the scratch directory the harness names for this session, under a file name unique to this agent and concern, such as `commit-<concern-slug>-<agent-session-id>.txt`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS: pass the file with `git commit -F <message-file>`, with the path written out literally.
- NEVER: remove the message file; the harness clears its scratch directory.
- NEVER: place the message file in the repository, in a fixed path, or in a directory shared by other sessions.

</message_payload>

<message_format>

Subject line: `<type>[(scope)]: <description>` in imperative mood, 50 characters at most, no period. A body, when present, explains WHAT and WHY, not HOW.

</message_format>

<commit_types>

Use the Conventional Commits types, plus `spec` for specification-only changes, and any custom type the product's AGENTS.md or commit-standards.md defines.

**NEVER USE `chore:`.** Everything has a purpose; use the specific type instead.

</commit_types>

<description_principles>

**Write for the reader, not the writer.** Someone scanning `git log --oneline` needs to understand what changed without opening the commit.

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

The type already names the kind of change:

```text
# ❌ Redundant - prefix already says it's a spec
spec(session): add session management spec
spec(auth): define auth feature stories

# ✅ Just describe the content
spec(session): specify timeout and cleanup behaviors
spec(auth): specify OAuth2 token lifecycle
```

**Good Examples**

```text
feat(parser): add support for nested expressions

Enables users to write complex queries with unlimited nesting depth.
Previously limited to 3 levels.

Refs: #234
```

```text
fix: return defaults for empty config

Return sensible defaults when config is missing or empty
instead of throwing unhandled exception.
```

```text
refactor: extract validation logic into separate module

Prepares codebase for L1 testing by isolating validation
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

</description_principles>

<failure_modes>

**Failure 1: A failing check stranded a dirty tree.**

What happened: Claude refused to commit session-owned changes because deterministic verification was red, so the dirty tree could be neither cleared nor rebased.

Why it failed: A red verification state was treated as a reason to withhold a local commit.

How to avoid: Record `Verification: failing`, create the atomic checkpoint, and report the failing state in the result.

**Failure 2: Missing verification blocked a recovery checkpoint.**

What happened: Claude required a fresh validation run before preserving work even though the immediate need was a local checkpoint for recovery or context loading.

Why it failed: An unrun verification was used as commit authority instead of a recorded state.

How to avoid: Record `Verification: not-run`, create the checkpoint, and include the product verification command in the result.

**Failure 3: A hook rejection was treated as permission to bypass hooks.**

What happened: A pre-commit hook rejected the staged concern and Claude attempted to preserve the checkpoint with `--no-verify`.

Why it failed: Commit availability never overrides repository hook policy.

How to avoid: Preserve the hook output, report that no commit was created, repair the hook failure through its governing workflow, and retry with hooks enabled.

</failure_modes>

# specs/ Directory Guide (LEGACY)

> **⚠️ LEGACY SYSTEM**: The `specs/` directory structure is legacy. New projects use the Outcome Engineering framework with `spx/` directory. This guide applies ONLY to projects that still use `specs/`.

## 🚨 DISAMBIGUATION: specs/ vs spx/

**Before proceeding, determine which system this project uses:**

| Directory | System                        | Skills to Use                                       |
| --------- | ----------------------------- | --------------------------------------------------- |
| `specs/`  | Legacy                        | `specs:understanding-specs`, `specs:managing-specs` |
| `spx/`    | Outcome Engineering framework | `spx:understanding-spx`, `spx:managing-spx`         |

**If BOTH directories exist**: Ask the user which system they want to work with.

**If NEITHER exists**: Ask the user if they want to set up specs (legacy) or spx (Outcome Engineering framework).

**Fully qualified skill names** (required when both plugins are installed):

```bash
# Legacy specs/ projects
/specs:understanding-specs
/specs:managing-specs

# Outcome Engineering framework spx/ projects
/spx:understanding-spx
/spx:managing-spx
```

---

This guide explains WHEN to invoke specs skills. It is a **router** that tells you which skill to use. The skills themselves contain the HOW (detailed procedures, templates, structure definitions).

---

## 🚨 MANDATORY SKILL INVOCATION RULES

**YOU MUST STOP AND INVOKE THE APPROPRIATE SKILL BEFORE PROCEEDING.**

Do NOT grep for templates.
Do NOT search for structure definitions.
Do NOT copy patterns you find in the repository.
Do NOT guess at requirements patterns.

DO use the skills as described below.

**The skills are the only authoritative source.**

---

## 🚨 CRITICAL: BSP Numbers Are SIBLING-UNIQUE, Not Global

**BSP numbers (capability-NN, feature-NN, story-NN) are ONLY unique among siblings at the same level.**

```text
capability-21/feature-32/story-54  ← One story-54
capability-28/feature-32/story-54  ← DIFFERENT story-54
capability-21/feature-87/story-54  ← DIFFERENT story-54
```

**ALWAYS use the FULL PATH when referencing work items:**

| ❌ WRONG (Ambiguous)     | ✅ CORRECT (Unambiguous)                     |
| ------------------------ | -------------------------------------------- |
| "story-54"               | "capability-21/feature-54/story-54"          |
| "implement feature-32"   | "implement capability-21/feature-32"         |
| "Continue with story-54" | "Continue capability-21/feature-54/story-54" |

**Why this matters:**

- Different capabilities can have identically-numbered features
- Different features can have identically-numbered stories
- "story-54" could refer to dozens of different stories across the codebase
- Without the full path, agents will access the WRONG work item

**When communicating about work items:**

1. Always include the full hierarchy path
2. Never use bare numbers like "story-54" without context
3. When in doubt, use the absolute path from `specs/work/`

---

## When to Invoke Skills

### Before Implementing ANY Work Item → `/specs:understanding-specs`

**⛔ BLOCKING REQUIREMENT: DO NOT PROCEED WITHOUT INVOKING THIS SKILL**

**Trigger conditions** (any of these):

- User says "implement story-NN", "work on feature-NN", or "build capability-NN"
- User references a work item file (e.g., "implement this.story.md")
- User asks you to write code for a story/feature/capability
- You see a work item path in `specs/work/doing/`
- You're about to write implementation code in a feature/story/capability scope

**What it does**: Loads complete context hierarchy (PRD/TRD → ADRs → work item → tests). Verifies all specification documents exist before implementation.

**Why mandatory**: Without this skill, you will miss requirements, violate ADRs, and implement the wrong thing.

**Example**:

```text
User: "Implement story-21_parse-flags"
→ STOP. DO NOT proceed to reading files or writing code.
→ IMMEDIATELY invoke: /understanding-specs specs/work/doing/.../story-21_parse-flags/parse-flags.story.md
→ WAIT for skill to load complete context
→ THEN proceed with implementation
```

---

### When Creating/Organizing Spec Structure → `/specs:managing-specs`

**⛔ BLOCKING REQUIREMENT: DO NOT PROCEED WITHOUT INVOKING THIS SKILL**

**Trigger conditions** (any of these):

- User says "create a PRD", "write a TRD", "add an ADR"
- User says "set up specs directory", "organize specs"
- User asks "what's the next work item to implement?"
- You need to understand BSP numbering or work item hierarchy
- You need ANY template (PRD/TRD/ADR/capability/feature/story)
- User asks about work item status (OPEN/IN_PROGRESS/DONE)

**What it does**: Provides access to all templates in the skill's `templates/` directory. Contains SPX framework structure, BSP numbering rules, status determination rules.

**Why mandatory**: Templates live in the skill directory (`.claude/plugins/cache/.../managing-specs/templates/`), NOT in the project. Searching the project will fail. The skill contains the complete structure definition.

**Example**:

```text
User: "Create a PRD for the new authentication feature"
→ STOP. DO NOT search for template files in the project.
→ DO NOT grep for "*.prd.md" files.
→ IMMEDIATELY invoke: /managing-specs
→ READ template from: ${CLAUDE_SKILL_DIR}/templates/requirements/product-change.prd.md
→ ADAPT template with authentication feature content
```

**Example**:

```text
User: "What should I work on next?"
→ STOP. DO NOT search for work items yourself.
→ IMMEDIATELY invoke: /managing-specs
→ ASK skill: "What's the next work item based on BSP ordering?"
→ Skill will identify first OPEN or IN_PROGRESS item
```

---

## Quick Reference: Skill Selection Decision Tree

| User Says...                           | YOU MUST INVOKE                              | DO NOT                                       |
| -------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| "Implement story-21"                   | `/specs:understanding-specs` (on story file) | Do NOT read story.md directly                |
| "Work on this feature"                 | `/specs:understanding-specs` (on feature)    | Do NOT start coding without context          |
| "Create a PRD"                         | `/specs:managing-specs`                      | Do NOT search project for PRD templates      |
| "Write an ADR"                         | `/specs:managing-specs`                      | Do NOT search project for ADR templates      |
| "What's next to work on?"              | `/specs:managing-specs`                      | Do NOT grep for work items yourself          |
| "Set up specs structure"               | `/specs:managing-specs`                      | Do NOT create directories without guidance   |
| "What's the status of feature-21?"     | `/specs:managing-specs`                      | Do NOT inspect `tests/` directories yourself |
| "Add a new capability/feature/story"   | `/specs:managing-specs`                      | Do NOT calculate BSP numbers yourself        |
| "Show me the PRD for this capability"  | `/specs:understanding-specs` (on capability) | Do NOT read PRD without loading full context |
| "How do I organize requirements docs?" | `/specs:managing-specs`                      | Do NOT invent your own structure             |

---

## Status and Work Item Rules Summary

**⚠️ For complete details, invoke `/specs:managing-specs` skill. Do NOT rely on this summary alone.**

### Key Principles

**BSP Numbering**: Lower number = must complete FIRST. You CANNOT work on item N until ALL items with numbers < N are DONE.

**Status Determination** (use CLI commands, do NOT check manually):

```bash
# View project status
spx spec status --format table

# Get next work item (respects BSP ordering)
spx spec next
```

Status values: OPEN, IN_PROGRESS, DONE

**Finding Next Work Item**: Run `spx spec next` or invoke `/specs:managing-specs`. Do NOT manually check for `DONE.md` files or inspect `tests/` directories yourself.

**Co-located Tests**:

Tests live with their specs and use suffix naming to indicate level:

- `specs/.../tests/*.unit.test.{ts,py}` - Unit tests (Level 1)
- `specs/.../tests/*.integration.test.{ts,py}` - Integration tests (Level 2)
- `specs/.../tests/*.e2e.test.{ts,py}` - E2E tests (Level 3)

Tests stay co-located permanently. No graduation to `tests/` directory.

---

## Session Management

Claude Code session handoffs are stored in:

```text
.spx/sessions/
├── TODO_*.md      # Available for /pickup
└── DOING_*.md     # Currently claimed
```

**Commands**:

- Use `/handoff` to create session context for continuation
- Use `/pickup` to load and claim a handoff

---

## Why These Rules Are Non-Negotiable

### Problem: Template Hallucination

Without invoking `/specs:managing-specs`, agents:

- Search the project for templates that don't exist there
- Find OLD PRDs/TRDs and copy their (possibly wrong) structure
- Invent their own template structure
- Miss critical sections required by the SPX framework

**Result**: Requirements documents that are incomplete or violate the framework.

### Problem: Context Gaps

Without invoking `/specs:understanding-specs`, agents:

- Miss parent PRD/TRD context
- Violate ADR decisions unknowingly
- Implement the wrong requirements
- Skip test requirements

**Result**: Code that doesn't match requirements and fails review.

### Problem: Structure Violations

Without invoking `/specs:managing-specs` for BSP numbering:

- Create work items with wrong numbers
- Violate dependency ordering
- Break the BSP algorithm (items can collide or be out of order)

**Result**: Work items that can't be ordered correctly, blocking downstream work.

---

## Verification Checklist

Before proceeding with ANY specs-related task:

- [ ] Did I invoke the correct skill?
- [ ] Did I wait for skill output before proceeding?
- [ ] Did I read templates from `${CLAUDE_SKILL_DIR}/templates/`, NOT from the project?
- [ ] Did I load complete context hierarchy for work items?
- [ ] Did I verify BSP numbering through the skill, not by calculating myself?

**If any checkbox is unchecked, STOP and invoke the skill.**

---

**For complete SPX framework structure, templates, and procedures**: Invoke `/specs:managing-specs` skill.

**For work item context loading and validation**: Invoke `/specs:understanding-specs` skill on the work item file.

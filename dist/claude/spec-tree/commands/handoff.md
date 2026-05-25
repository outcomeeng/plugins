---
name: handoff
description: Create timestamped handoff document for continuing work in a fresh context
argument-hint: "[--no-session] [--prune]"
allowed-tools:
  - Skill
---

<context>
**Arguments:** `$ARGUMENTS`

**Working Directory:**
!`pwd`

**Git Status:**
!`git status --short || echo "Not in a git repo"`

**Current Branch:**
!`git branch --show-current || echo "Not in a git repo"`

**Current Sessions:**
!`spx session list || echo 'Ask user to install spx CLI: "npm install --global @outcomeeng/spx"'`

**Spec Tree:**
!`ls spx/*.product.md 2>/dev/null || echo "No spec tree found"`
</context>

<objective>
Close the current work session through the canonical handoff protocol.

The command only gathers immediate context and delegates the workflow to `/handing-off`; the skill owns reflection, persistence decisions, commit gating, session creation, and pickup/archive coordination.
</objective>

<process>
Call the Skill tool now with the context above:

```json
Skill tool → { "skill": "spec-tree:handing-off", "args": "$ARGUMENTS" }
```

Do not run the handoff workflow manually. The skill is the source of truth.
</process>

<success_criteria>

- `/handing-off` is invoked with the original arguments
- No command-local handoff protocol is executed
- Any handoff, release, pruning, or commit gating behavior comes from the skill

</success_criteria>

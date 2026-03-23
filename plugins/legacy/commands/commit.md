---
allowed-tools: Skill
description: Commit following Conventional Commits
argument-hint: [files-to-stage]
---

# Commit Context

**Arguments:** `$ARGUMENTS`

**Current branch:**
!`git branch --show-current`

**Status:**
!`git status --short`

**Staged changes:**
!`git diff --cached --stat`

**Unstaged changes:**
!`git diff --stat`

**Recent commits (for style reference):**
!`git log --oneline -5`

---

## ACTION REQUIRED

**Call the Skill tool NOW** with the context above:

```json
Skill tool → { "skill": "core:committing-changes" }
```

Do NOT proceed manually. The skill contains the commit protocol.

---
allowed-tools: Skill
description: Commit following Conventional Commits
argument-hint: [files-to-stage]
---

# Commit Context

**Arguments:** `$ARGUMENTS`

**Current branch:**
!`git branch --show-current || echo 'Not a git repo'`

**Status:**
!`git status --short || echo 'Not a git repo'`

**Staged changes:**
!`git diff --cached --stat || echo 'Not a git repo'`

**Unstaged changes:**
!`git diff --stat || echo 'Not a git repo'`

**Recent commits (for style reference):**
!`git log --oneline -5 || echo 'Not a git repo'`

---

## ACTION REQUIRED

**Call the Skill tool NOW** with the context above:

```json
Skill tool → { "skill": "spec-tree:committing-changes" }
```

Do NOT proceed manually. The skill contains the commit protocol.

---
allowed-tools: Skill
description: Open a draft PR for the current branch with curated title and body
argument-hint: [scope-hint]
---

# Open PR Context

**Arguments:** `$ARGUMENTS`

**gh auth status:**
!`gh auth status 2>&1 | head -5`

**Current branch:**
!`git branch --show-current || echo 'Not a git repo'`

**Default base branch:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '(gh not authenticated or repo not detected)'`

**Working tree state (empty = clean):**
!`git status --porcelain || echo 'Not a git repo'`

**Commits ahead of base:**
!`base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null); git log --oneline "origin/${base:-main}..HEAD" 2>/dev/null | head -20 || echo '(no commits ahead, or base ref missing)'`

**Diff stats vs base:**
!`base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null); git diff "origin/${base:-main}...HEAD" --stat 2>/dev/null | tail -5 || echo '(no diff)'`

**Existing PR for current branch:**
!`gh pr view --json url --jq '.url' 2>/dev/null || echo '(no existing PR)'`

---

## ACTION REQUIRED

**Call the Skill tool NOW** with the context above:

```json
Skill tool → { "skill": "spec-tree:opening-pr" }
```

Do NOT proceed manually. The skill contains the PR-opening protocol — title and body conventions, the `gh pr create --draft` flow, and the handoff to `/managing-pr` for the post-creation review loop. Cross-cutting merge-flow standards (branch hygiene, branch topology, push semantics, draft lifecycle, heartbeat, two-surface review inspection) live in `/standardizing-merging`, which `opening-pr` loads automatically.

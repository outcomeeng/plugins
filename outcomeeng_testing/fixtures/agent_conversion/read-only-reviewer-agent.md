---
name: read-only-reviewer
description: Guarded writer.
profile: strong
permissionMode: bypassPermissions
tools:
  - Read
disallowedTools:
  - Bash
skills:
  - instructions:audit-subagent
unknownField: keep-me-visible
---

Review write behavior.

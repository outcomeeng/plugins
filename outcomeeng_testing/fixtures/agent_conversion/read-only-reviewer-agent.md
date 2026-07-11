---
name: read-only-reviewer
description: Guarded writer.
model: opus
permissionMode: bypassPermissions
tools:
  - Read
disallowedTools:
  - Bash
skills:
  - develop:audit-subagents
unknownField: keep-me-visible
---

Review write behavior.

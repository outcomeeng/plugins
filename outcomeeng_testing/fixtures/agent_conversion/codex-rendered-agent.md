---
name: changes-reviewer
description: Review changes.
profile: standard
sandbox_mode: read-only
nickname_candidates: [Atlas, Delta]
mcp_servers:
  docs:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-docs"
skills:
  - spec-tree:review-changes
tools: Read
---

Review the diff and report findings.

---
name: changes-reviewer
description: Review changes.
model: gpt-5.4
model_reasoning_effort: high
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

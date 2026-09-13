---
name: changes-reviewer
description: Review changes.
profile: standard
mcp_servers:
  docs:
    command: npx
    startup_timeout_sec: 20
    enabled: false
    required: true
    env_vars:
      - LOCAL_TOKEN
      - name: REMOTE_TOKEN
        source: remote
    args:
      - -y
      - "@modelcontextprotocol/server-docs"
---

Review the diff and report findings.

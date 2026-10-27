---
name: inheriting-conforming
description: Fixture definition with a tools allowlist whose Codex rendering alone declares a native permission field.
tools: Read, Grep, Glob
profile: standard
{!% if target == 'codex' %!}
sandbox_mode: read-only
{!% endif %!}
---

Fixture body.

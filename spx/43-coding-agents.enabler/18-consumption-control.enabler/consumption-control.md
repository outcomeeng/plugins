---
id: 019e49f2-4700-7c15-a810-a7883b427658
malleability: spec
---

# Consumption Control

PROVIDES deterministic consumption measurements, budget signals, and managed reporting for Claude Code agent sessions
SO THAT operators overseeing coding work
CAN inspect the behaviors driving consumption and detect spending bursts from durable local evidence

## Assertions

- Every collection invocation imports a bounded portion of the configured reset week or advances durable transcript offsets, reconciles streaming updates and late rows by stable request identity, and reports incomplete coverage explicitly while preserving the original transcripts.
- Every frozen half-open UTC measurement reconciles requests, sessions, models, and native parent/subagent relationships across uncached input, cache reads, cache creation, output, and estimated API-equivalent cost; unsupported pricing remains explicit.
- HTML, JSON, and CSV reports share one measurement result and expose session/model shares, early-versus-late context, cache behavior, bounded tool-result evidence, and durable transcript references; unsupported skill, plugin, MCP, file, and useful-output attribution is unknown.
- The detector records advisory signals for the rolling fifteen-minute threshold, reset-anchored weekly budget, and elapsed-period spending pace with the exact measured window and effective configuration; API-equivalent amounts establish no conversion to subscription allowance.
- An explicitly activated macOS installation runs finite detector and hourly report workers from stable versioned assets, excludes overlapping work, persists restart state and alert identities, bounds retention, and exposes failures through inspectable install, status, stop, and restart operations.
- Explicitly selected, version-checked existing-index investigation is bounded and optional; an absent or incompatible investigation tool preserves deterministic accounting and records the gap.
- Installed skill scripts under `src/plugins/coding-agents/skills/control-token-spend/` use standard-library Python at the supported floor, make no model calls, require no TraceRoost or SPX usage-evidence service, preserve required gates and resource ceilings, and attribute verified output only from Applied store state, default-branch merge evidence, or current passing pinned evidence.
